#!/usr/bin/env python3
"""
Analysis: Skills Demand by Location
Analyzes which skills are in demand in different locations
"""

import pymysql
import json
import sys
import os

# Add parent directory to path to import data_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.data_utils import extract_skills, parse_salary, normalize_location

from collections import defaultdict, Counter
from statistics import mean

def get_related_jobs(connection, location, skill, limit=5):
    """Get related available jobs for this location and skill"""
    try:
        cursor = connection.cursor()
        query = """SELECT title, company, location, salary, job_id FROM jobs_latest 
                   WHERE location LIKE %s AND (tags_and_skills LIKE %s OR job_description LIKE %s) LIMIT %s"""
        location_pattern = f"%{location}%"
        skill_pattern = f"%{skill}%"
        cursor.execute(query, (location_pattern, skill_pattern, skill_pattern, limit))
        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id']} for job in jobs]
        return json.dumps(related_jobs)
    except Exception as e:
        print(f"Error getting related jobs: {e}")
        return "[]"

def run_analysis(connection):
    """Main analysis function"""
    try:
        cursor = connection.cursor()

        print("🔍 Fetching job data for location-skills analysis...")

        query = """SELECT location, tags_and_skills, job_description, salary, salary_detail FROM jobs_complete 
                   WHERE location IS NOT NULL AND location != '' 
                   AND (tags_and_skills IS NOT NULL OR job_description IS NOT NULL)"""
        cursor.execute(query)
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found with location and skills data")
            return False

        print(f"📊 Processing {len(jobs)} jobs with location and skills data...")

        location_skill_data = defaultdict(lambda: defaultdict(lambda: {'frequency': 0, 'job_count': 0, 'salaries': []}))

        processed_jobs = 0

        for job in jobs:
            location = normalize_location(job['location'])
            if location != "Unknown" and len(location) > 2:
                # Extract skills from both fields
                skills = extract_skills(job.get('tags_and_skills'))
                if job.get('job_description'):
                    skills.extend(extract_skills(job['job_description']))

                # Remove duplicates and limit skill length
                unique_skills = []
                seen = set()
                for skill in skills:
                    if (skill.lower() not in seen and 
                        len(skill) > 2 and len(skill) <= 100 and 
                        len(skill.split()) <= 4):  # Limit to reasonable skill names
                        unique_skills.append(skill)
                        seen.add(skill.lower())

                salary_value = parse_salary(job.get('salary'), job.get('salary_detail'))

                for skill in unique_skills:
                    location_skill_data[location][skill]['frequency'] += 1
                    location_skill_data[location][skill]['job_count'] += 1

                    if salary_value and salary_value > 0:
                        location_skill_data[location][skill]['salaries'].append(salary_value)

                processed_jobs += 1

        print(f"✅ Successfully processed {processed_jobs} jobs")
        print("💾 Clearing previous analysis results...")

        cursor.execute("DELETE FROM analysis_skills_by_location")
        results_stored = 0

        print("📈 Analyzing skills demand by location...")

        for location, skills_data in location_skill_data.items():
            # Only consider locations with meaningful data (at least 10 different skills)
            if len(skills_data) >= 10:
                # Get top skills for this location
                top_skills = sorted(skills_data.items(), key=lambda x: x[1]['frequency'], reverse=True)[:25]

                for skill, data in top_skills:
                    if data['frequency'] >= 3:  # Only skills mentioned at least 3 times
                        # Ensure skill length is within database limits
                        if len(skill) > 100:
                            skill = skill[:97] + "..."

                        avg_salary = mean(data['salaries']) if data['salaries'] else 0
                        related_jobs = get_related_jobs(connection, location, skill)

                        insert_query = """
                        INSERT INTO analysis_skills_by_location 
                        (location, skill, frequency, job_count, avg_salary, related_jobs)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """

                        cursor.execute(insert_query, (
                            location, skill, data['frequency'], data['job_count'],
                            round(avg_salary, 2), related_jobs
                        ))
                        results_stored += 1

        print(f"✅ Analysis completed! Stored {results_stored} location-skill records")

        # Print summary
        print("\n🌍 Top Locations for Skills Analysis:")
        location_counts = {loc: len(skills) for loc, skills in location_skill_data.items() if len(skills) >= 10}
        sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        for location, skill_count in sorted_locations:
            total_jobs = sum(skill_data['job_count'] for skill_data in location_skill_data[location].values())
            print(f"  • {location}: {skill_count} unique skills, {total_jobs} job opportunities")

        return True

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from analysis_runner import DB_CONFIG

    connection = pymysql.connect(**DB_CONFIG)
    success = run_analysis(connection)
    connection.close()

    if success:
        print("✅ Analysis test completed successfully")
    else:
        print("❌ Analysis test failed")
