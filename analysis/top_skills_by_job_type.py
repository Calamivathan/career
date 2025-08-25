#!/usr/bin/env python3
"""
Analysis: Top Skills by Job Type
Analyzes the most required skills for each job type/category
"""

import pymysql
import json
import sys
import os
# Add parent directory to path to import data_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.data_utils import extract_skills, parse_salary

from collections import defaultdict, Counter

def normalize_job_title(title):
    """Normalize job titles to group similar ones"""
    if not title:
        return "Unknown"

    title_lower = title.lower()

    # Define job categories
    if any(keyword in title_lower for keyword in ['engineer', 'developer', 'programmer']):
        if 'data' in title_lower:
            return 'Data Engineer/Developer'
        elif any(keyword in title_lower for keyword in ['software', 'backend', 'frontend', 'full stack']):
            return 'Software Engineer/Developer'
        elif 'ai' in title_lower or 'ml' in title_lower or 'machine learning' in title_lower:
            return 'AI/ML Engineer'
        elif 'qa' in title_lower or 'test' in title_lower:
            return 'QA/Test Engineer'
        else:
            return 'Engineer/Developer'
    elif 'analyst' in title_lower:
        if 'data' in title_lower:
            return 'Data Analyst'
        elif 'business' in title_lower:
            return 'Business Analyst'
        else:
            return 'Analyst'
    elif any(keyword in title_lower for keyword in ['manager', 'lead', 'head']):
        return 'Management/Leadership'
    elif 'scientist' in title_lower:
        return 'Data Scientist'
    elif any(keyword in title_lower for keyword in ['intern', 'trainee']):
        return 'Internship/Trainee'
    elif any(keyword in title_lower for keyword in ['consultant', 'advisor']):
        return 'Consultant/Advisor'
    elif any(keyword in title_lower for keyword in ['designer', 'ui', 'ux']):
        return 'Design/UX'
    elif any(keyword in title_lower for keyword in ['marketing', 'sales']):
        return 'Marketing/Sales'
    else:
        return 'Other'

def get_related_jobs(connection, job_type, limit=5):
    """Get related available jobs for this job type"""
    try:
        cursor = connection.cursor()

        query = """
        SELECT title, company, location, salary, job_id
        FROM jobs_latest 
        WHERE title LIKE %s 
        LIMIT %s
        """

        # Create search pattern for job type
        search_pattern = f"%{job_type.split('/')[0].lower()}%"
        cursor.execute(query, (search_pattern, limit))

        jobs = cursor.fetchall()
        related_jobs = []

        for job in jobs:
            job_info = {
                'title': job['title'],
                'company': job['company'], 
                'location': job['location'],
                'salary': job['salary'],
                'job_id': job['job_id']
            }
            related_jobs.append(job_info)

        return json.dumps(related_jobs)
    except Exception as e:
        print(f"Error getting related jobs: {e}")
        return "[]"

def run_analysis(connection):
    """Main analysis function"""
    try:
        cursor = connection.cursor()

        print("🔍 Fetching job data for skills analysis...")

        # Fetch all jobs from complete data
        query = """
        SELECT title, tags_and_skills, job_description, salary, salary_detail
        FROM jobs_complete 
        WHERE (tags_and_skills IS NOT NULL AND tags_and_skills != '') 
        OR (job_description IS NOT NULL AND job_description != '')
        """

        cursor.execute(query)
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found with skills data")
            return False

        print(f"📊 Processing {len(jobs)} jobs...")

        # Group skills by job type
        job_type_skills = defaultdict(list)
        job_type_counts = defaultdict(int)
        job_type_salaries = defaultdict(list)

        processed_jobs = 0

        for job in jobs:
            job_type = normalize_job_title(job['title'])
            job_type_counts[job_type] += 1

            # Extract skills from tags_and_skills
            skills = extract_skills(job.get('tags_and_skills'))

            # Also extract from job description if available
            if job.get('job_description'):
                desc_skills = extract_skills(job['job_description'])
                skills.extend(desc_skills)

            # Remove duplicates while preserving order
            unique_skills = []
            seen = set()
            for skill in skills:
                if skill.lower() not in seen and len(skill) <= 100:  # Limit skill length
                    unique_skills.append(skill)
                    seen.add(skill.lower())

            job_type_skills[job_type].extend(unique_skills)

            # Parse salary using new utility
            salary_value = parse_salary(job.get('salary'), job.get('salary_detail'))
            if salary_value and salary_value > 0:
                job_type_salaries[job_type].append(salary_value)

            processed_jobs += 1

        print(f"✅ Successfully processed {processed_jobs} jobs")
        print("💾 Clearing previous analysis results...")

        # Clear previous results
        cursor.execute("DELETE FROM analysis_top_skills_by_job_type")

        print("📈 Analyzing top skills for each job type...")

        # Analyze and store results
        results_stored = 0

        for job_type, skills_list in job_type_skills.items():
            if job_type_counts[job_type] < 3:  # Skip job types with too few jobs
                continue

            # Count skills frequency
            skill_counter = Counter(skills_list)

            # Get top 15 skills for this job type
            top_skills = skill_counter.most_common(15)

            for skill, frequency in top_skills:
                if len(skill) > 100:  # Double check skill length
                    skill = skill[:97] + "..."

                percentage = (frequency / job_type_counts[job_type]) * 100

                # Get related jobs
                related_jobs = get_related_jobs(connection, job_type)

                # Insert into database
                insert_query = """
                INSERT INTO analysis_top_skills_by_job_type 
                (job_type, skill, frequency, percentage, related_jobs)
                VALUES (%s, %s, %s, %s, %s)
                """

                cursor.execute(insert_query, (
                    job_type,
                    skill,
                    frequency,
                    round(percentage, 2),
                    related_jobs
                ))

                results_stored += 1

        print(f"✅ Analysis completed! Stored {results_stored} skill-job type combinations")
        print(f"📋 Analyzed {len(job_type_skills)} job types")

        # Print summary
        print("\n📊 Top Job Types by Volume:")
        sorted_types = sorted(job_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for job_type, count in sorted_types:
            avg_salary = 0
            if job_type in job_type_salaries and job_type_salaries[job_type]:
                avg_salary = sum(job_type_salaries[job_type]) / len(job_type_salaries[job_type])
            print(f"  • {job_type}: {count} jobs (Avg: {avg_salary/100000:.1f} LPA)")

        return True

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test the analysis
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
