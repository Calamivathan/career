#!/usr/bin/env python3
"""
Analysis: Trending Skills Analysis
Analyzes which skills are trending/growing in demand over time
"""

import pymysql
import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta

def extract_skills_from_text(text):
    """Extract skills from tags_and_skills and job_description"""
    if not text:
        return []

    skills = []
    if isinstance(text, str):
        parts = re.split(r'[,;|]', text)
        for part in parts:
            skill = part.strip()
            if skill and len(skill) > 1:
                skills.append(skill.title())

    return skills

def get_related_jobs(connection, skill, limit=5):
    """Get related available jobs that require this skill"""
    try:
        cursor = connection.cursor()

        query = """
        SELECT title, company, location, salary, job_id
        FROM jobs_latest 
        WHERE tags_and_skills LIKE %s OR job_description LIKE %s
        LIMIT %s
        """

        skill_pattern = f"%{skill.lower()}%"
        cursor.execute(query, (skill_pattern, skill_pattern, limit))

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

def calculate_growth_rate(old_count, new_count):
    """Calculate growth rate percentage"""
    if old_count == 0:
        return 100.0 if new_count > 0 else 0.0
    return ((new_count - old_count) / old_count) * 100

def run_analysis(connection):
    """Main analysis function"""
    try:
        cursor = connection.cursor()

        print("🔍 Fetching job data for trending skills analysis...")

        # Calculate date thresholds
        now = datetime.now()
        six_months_ago = now - timedelta(days=180)
        one_year_ago = now - timedelta(days=365)

        # Fetch recent jobs (last 6 months)
        recent_query = """
        SELECT tags_and_skills, job_description, created_at
        FROM jobs_complete 
        WHERE created_at >= %s
        AND (tags_and_skills IS NOT NULL AND tags_and_skills != '')
        """

        cursor.execute(recent_query, (six_months_ago.strftime('%Y-%m-%d'),))
        recent_jobs = cursor.fetchall()

        # Fetch older jobs (6-12 months ago)
        older_query = """
        SELECT tags_and_skills, job_description, created_at
        FROM jobs_complete 
        WHERE created_at >= %s AND created_at < %s
        AND (tags_and_skills IS NOT NULL AND tags_and_skills != '')
        """

        cursor.execute(older_query, (one_year_ago.strftime('%Y-%m-%d'), six_months_ago.strftime('%Y-%m-%d')))
        older_jobs = cursor.fetchall()

        print(f"📊 Processing {len(recent_jobs)} recent jobs and {len(older_jobs)} older jobs...")

        if not recent_jobs and not older_jobs:
            print("No jobs found with date information")
            return False

        # Count skills in each period
        recent_skills = Counter()
        older_skills = Counter()

        # Process recent jobs
        for job in recent_jobs:
            skills = extract_skills_from_text(job['tags_and_skills'])
            if job['job_description']:
                skills.extend(extract_skills_from_text(job['job_description']))

            for skill in skills:
                recent_skills[skill] += 1

        # Process older jobs
        for job in older_jobs:
            skills = extract_skills_from_text(job['tags_and_skills'])
            if job['job_description']:
                skills.extend(extract_skills_from_text(job['job_description']))

            for skill in skills:
                older_skills[skill] += 1

        print("💾 Clearing previous analysis results...")

        # Clear previous results
        cursor.execute("DELETE FROM analysis_trending_skills")

        print("📈 Calculating skill trends...")

        # Calculate trends
        all_skills = set(recent_skills.keys()) | set(older_skills.keys())
        trending_skills = []

        for skill in all_skills:
            recent_count = recent_skills.get(skill, 0)
            older_count = older_skills.get(skill, 0)

            # Only consider skills with meaningful data
            if recent_count >= 5 or older_count >= 5:
                growth_rate = calculate_growth_rate(older_count, recent_count)

                trending_skills.append({
                    'skill': skill,
                    'recent_count': recent_count,
                    'older_count': older_count,
                    'growth_rate': growth_rate,
                    'total_frequency': recent_count + older_count
                })

        # Sort by growth rate and current frequency
        trending_skills.sort(key=lambda x: (x['growth_rate'], x['recent_count']), reverse=True)

        # Store top trending skills
        results_stored = 0

        for skill_data in trending_skills[:50]:  # Top 50 trending skills
            related_jobs = get_related_jobs(connection, skill_data['skill'])

            # Determine trend period description
            if skill_data['growth_rate'] > 100:
                trend_period = "Rapidly Growing (>100%)"
            elif skill_data['growth_rate'] > 50:
                trend_period = "High Growth (50-100%)"
            elif skill_data['growth_rate'] > 20:
                trend_period = "Moderate Growth (20-50%)"
            elif skill_data['growth_rate'] > 0:
                trend_period = "Slight Growth (0-20%)"
            else:
                trend_period = "Declining"

            insert_query = """
            INSERT INTO analysis_trending_skills 
            (skill, current_frequency, growth_rate, trend_period, related_jobs)
            VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(insert_query, (
                skill_data['skill'],
                skill_data['recent_count'],
                round(skill_data['growth_rate'], 2),
                trend_period,
                related_jobs
            ))

            results_stored += 1

        print(f"✅ Analysis completed! Stored {results_stored} trending skills")

        # Print summary of top trending skills
        print("\n🚀 Top 10 Trending Skills:")
        for i, skill_data in enumerate(trending_skills[:10], 1):
            print(f"  {i}. {skill_data['skill']}: {skill_data['growth_rate']:.1f}% growth ({skill_data['recent_count']} recent mentions)")

        # Print top declining skills
        declining_skills = [s for s in trending_skills if s['growth_rate'] < -20][:5]
        if declining_skills:
            print("\n📉 Top Declining Skills:")
            for i, skill_data in enumerate(declining_skills, 1):
                print(f"  {i}. {skill_data['skill']}: {skill_data['growth_rate']:.1f}% decline")

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
