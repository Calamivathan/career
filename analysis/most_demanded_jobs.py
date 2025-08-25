#!/usr/bin/env python3
"""
Analysis: Most Demanded Jobs
Analyzes jobs with highest application counts and demand ratios
"""

import pymysql
import json
from collections import defaultdict

def normalize_job_title(title):
    """Normalize job titles for grouping"""
    if not title:
        return "Unknown"

    title_lower = title.lower()

    if any(keyword in title_lower for keyword in ['engineer', 'developer', 'programmer']):
        if 'data' in title_lower:
            return 'Data Engineer/Developer'
        elif any(keyword in title_lower for keyword in ['software', 'backend', 'frontend']):
            return 'Software Engineer/Developer'
        elif 'ai' in title_lower or 'ml' in title_lower:
            return 'AI/ML Engineer'
        elif 'qa' in title_lower or 'test' in title_lower:
            return 'QA/Test Engineer'
        else:
            return 'Engineer/Developer'
    elif 'analyst' in title_lower:
        return 'Data Analyst' if 'data' in title_lower else 'Business Analyst'
    elif any(keyword in title_lower for keyword in ['manager', 'lead']):
        return 'Management/Leadership'
    elif 'scientist' in title_lower:
        return 'Data Scientist'
    elif any(keyword in title_lower for keyword in ['intern', 'trainee']):
        return 'Internship/Trainee'
    else:
        return title.title()

def get_related_jobs(connection, job_title_pattern, limit=5):
    """Get related available jobs"""
    try:
        cursor = connection.cursor()

        query = """
        SELECT title, company, location, salary, job_id, apply_count, openings
        FROM jobs_latest 
        WHERE title LIKE %s 
        ORDER BY CAST(apply_count AS UNSIGNED) DESC
        LIMIT %s
        """

        search_pattern = f"%{job_title_pattern.split('/')[0].lower()}%"
        cursor.execute(query, (search_pattern, limit))

        jobs = cursor.fetchall()
        related_jobs = []

        for job in jobs:
            job_info = {
                'title': job['title'],
                'company': job['company'], 
                'location': job['location'],
                'salary': job['salary'],
                'job_id': job['job_id'],
                'apply_count': job.get('apply_count', 0),
                'openings': job.get('openings', 1)
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

        print("🔍 Fetching job data for demand analysis...")

        # Fetch jobs with application and opening data
        query = """
        SELECT title, apply_count, openings, company, location
        FROM jobs_complete 
        WHERE apply_count IS NOT NULL 
        AND apply_count > 0
        AND openings IS NOT NULL
        AND openings > 0
        """

        cursor.execute(query)
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found with application/opening data")
            return False

        print(f"📊 Processing {len(jobs)} jobs with demand data...")

        # Group by job title and aggregate data
        job_demand_data = defaultdict(lambda: {
            'total_applications': 0,
            'total_openings': 0,
            'job_count': 0,
            'companies': set(),
            'locations': set()
        })

        for job in jobs:
            try:
                apply_count = int(job['apply_count']) if job['apply_count'] else 0
                openings = int(job['openings']) if job['openings'] else 1

                if apply_count > 0 and openings > 0:
                    normalized_title = normalize_job_title(job['title'])

                    job_demand_data[normalized_title]['total_applications'] += apply_count
                    job_demand_data[normalized_title]['total_openings'] += openings
                    job_demand_data[normalized_title]['job_count'] += 1

                    if job['company']:
                        job_demand_data[normalized_title]['companies'].add(job['company'])
                    if job['location']:
                        job_demand_data[normalized_title]['locations'].add(job['location'])

            except (ValueError, TypeError):
                continue

        # Calculate demand metrics
        demand_analysis = []

        for job_title, data in job_demand_data.items():
            if data['job_count'] >= 3:  # Only consider jobs with meaningful data
                demand_ratio = data['total_applications'] / data['total_openings']
                avg_competition = data['total_applications'] / data['job_count']

                demand_analysis.append({
                    'job_title': job_title,
                    'total_applications': data['total_applications'],
                    'total_openings': data['total_openings'],
                    'demand_ratio': demand_ratio,
                    'avg_competition': avg_competition,
                    'job_count': data['job_count']
                })

        # Sort by total applications (most demanded)
        demand_analysis.sort(key=lambda x: x['total_applications'], reverse=True)

        print("💾 Clearing previous analysis results...")

        # Clear previous results
        cursor.execute("DELETE FROM analysis_most_demanded_jobs")

        print("📈 Storing demand analysis results...")

        # Store results
        results_stored = 0

        for demand_data in demand_analysis:
            related_jobs = get_related_jobs(connection, demand_data['job_title'])

            insert_query = """
            INSERT INTO analysis_most_demanded_jobs 
            (job_title, total_applications, total_openings, demand_ratio, avg_competition, related_jobs)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(insert_query, (
                demand_data['job_title'],
                demand_data['total_applications'],
                demand_data['total_openings'],
                round(demand_data['demand_ratio'], 2),
                round(demand_data['avg_competition'], 2),
                related_jobs
            ))

            results_stored += 1

        print(f"✅ Analysis completed! Stored {results_stored} job demand records")

        # Print summary
        print("\n🔥 Top 10 Most Demanded Jobs (by applications):")
        for i, demand_data in enumerate(demand_analysis[:10], 1):
            print(f"  {i}. {demand_data['job_title']}: {demand_data['total_applications']:,} applications")
            print(f"      Demand ratio: {demand_data['demand_ratio']:.1f} applications per opening")

        # Print highest competition jobs
        high_competition = sorted(demand_analysis, key=lambda x: x['demand_ratio'], reverse=True)[:5]
        print("\n🥵 Most Competitive Jobs (highest demand ratio):")
        for i, demand_data in enumerate(high_competition, 1):
            print(f"  {i}. {demand_data['job_title']}: {demand_data['demand_ratio']:.1f} applications per opening")

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
