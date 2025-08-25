#!/usr/bin/env python3
"""
Analysis: Top Paying Jobs
Analyzes the highest paying job positions and salary ranges
"""

import pymysql
import json
import sys
import os

# Add parent directory to path to import data_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.data_utils import parse_salary

from collections import defaultdict
from statistics import mean, median

def normalize_job_title(title):
    """Normalize job titles for grouping"""
    if not title:
        return "Unknown"

    title_lower = title.lower()

    # Define categories with more specific matching
    if any(keyword in title_lower for keyword in ['cto', 'ceo', 'director', 'vp', 'vice president']):
        return 'C-Level/Executive'
    elif any(keyword in title_lower for keyword in ['senior manager', 'senior lead', 'principal manager']):
        return 'Senior Management'
    elif any(keyword in title_lower for keyword in ['manager', 'lead', 'head']) and 'assistant' not in title_lower:
        return 'Management/Lead'
    elif any(keyword in title_lower for keyword in ['senior engineer', 'senior developer', 'sr engineer', 'senior software']):
        return 'Senior Engineer/Developer'
    elif any(keyword in title_lower for keyword in ['architect', 'principal engineer', 'staff engineer']):
        return 'Architect/Principal Engineer'
    elif 'data scientist' in title_lower:
        return 'Data Scientist'
    elif any(keyword in title_lower for keyword in ['ml engineer', 'ai engineer', 'machine learning engineer']):
        return 'AI/ML Engineer'
    elif any(keyword in title_lower for keyword in ['software engineer', 'developer', 'programmer']) and 'senior' not in title_lower:
        return 'Software Engineer/Developer'
    elif 'consultant' in title_lower:
        return 'Consultant'
    elif 'analyst' in title_lower:
        if 'data' in title_lower:
            return 'Data Analyst'
        elif 'business' in title_lower:
            return 'Business Analyst'
        else:
            return 'Analyst'
    elif any(keyword in title_lower for keyword in ['intern', 'trainee']):
        return 'Internship/Trainee'
    else:
        # Keep original title if it doesn't fit categories (but clean it up)
        return title.title()[:100]  # Limit length for database

def get_related_jobs(connection, job_title_pattern, limit=5):
    """Get related available jobs for this job title pattern"""
    try:
        cursor = connection.cursor()

        query = """
        SELECT title, company, location, salary, job_id
        FROM jobs_latest 
        WHERE title LIKE %s 
        ORDER BY CAST(REGEXP_REPLACE(REGEXP_REPLACE(COALESCE(salary, '0'), '[^0-9.]', ''), '^0+', '') AS DECIMAL(15,2)) DESC
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

        print("🔍 Fetching job data for salary analysis...")

        # Fetch all jobs with salary information
        query = """
        SELECT title, salary, salary_detail, company, location
        FROM jobs_complete 
        WHERE (salary IS NOT NULL AND salary != '' AND salary != 'Not Disclosed')
        OR (salary_detail IS NOT NULL AND salary_detail != '')
        """

        cursor.execute(query)
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found with salary data")
            return False

        print(f"📊 Processing {len(jobs)} jobs with salary information...")

        # Group jobs by normalized title and collect salary data
        job_salary_data = defaultdict(list)

        processed_jobs = 0
        for job in jobs:
            # Use the improved salary parsing
            salary_value = parse_salary(job.get('salary'), job.get('salary_detail'))

            if salary_value and salary_value > 0:
                normalized_title = normalize_job_title(job['title'])
                job_salary_data[normalized_title].append({
                    'salary': salary_value,
                    'company': job['company'],
                    'location': job['location'],
                    'original_title': job['title']
                })
                processed_jobs += 1

        print(f"✅ Successfully processed {processed_jobs} jobs with valid salary data")

        # Calculate statistics for each job category
        job_statistics = []

        for job_title, salary_list in job_salary_data.items():
            if len(salary_list) >= 3:  # Only consider job types with at least 3 entries
                salaries = [item['salary'] for item in salary_list]

                avg_salary = mean(salaries)
                median_salary = median(salaries)
                min_salary = min(salaries)
                max_salary = max(salaries)
                job_count = len(salaries)

                # Filter out unrealistic salaries (basic validation)
                if 50000 <= avg_salary <= 50000000:  # Between 50k and 5 crore
                    job_statistics.append({
                        'job_title': job_title,
                        'avg_salary': avg_salary,
                        'median_salary': median_salary,
                        'min_salary': min_salary,
                        'max_salary': max_salary,
                        'job_count': job_count,
                        'salary_data': salary_list
                    })

        # Sort by average salary
        job_statistics.sort(key=lambda x: x['avg_salary'], reverse=True)

        print("💾 Clearing previous analysis results...")

        # Clear previous results
        cursor.execute("DELETE FROM analysis_top_paying_jobs")

        print("📈 Storing top paying jobs analysis...")

        # Store results
        results_stored = 0

        for job_stat in job_statistics:
            related_jobs = get_related_jobs(connection, job_stat['job_title'])

            insert_query = """
            INSERT INTO analysis_top_paying_jobs 
            (job_title, avg_salary, min_salary, max_salary, job_count, related_jobs)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(insert_query, (
                job_stat['job_title'],
                round(job_stat['avg_salary'], 2),
                round(job_stat['min_salary'], 2),
                round(job_stat['max_salary'], 2),
                job_stat['job_count'],
                related_jobs
            ))

            results_stored += 1

        print(f"✅ Analysis completed! Stored {results_stored} job categories")

        # Print summary of top paying jobs
        print("\n💰 Top 10 Highest Paying Jobs:")
        for i, job_stat in enumerate(job_statistics[:10], 1):
            avg_lpa = job_stat['avg_salary'] / 100000
            median_lpa = job_stat['median_salary'] / 100000
            print(f"  {i:2d}. {job_stat['job_title']}: {avg_lpa:.1f} LPA avg, {median_lpa:.1f} LPA median ({job_stat['job_count']} jobs)")

        # Print salary ranges
        print("\n📊 Salary Distribution Summary:")
        total_categories = len(job_statistics)
        high_paying = sum(1 for stat in job_statistics if stat['avg_salary'] >= 1000000)
        mid_paying = sum(1 for stat in job_statistics if 500000 <= stat['avg_salary'] < 1000000)
        entry_paying = sum(1 for stat in job_statistics if stat['avg_salary'] < 500000)

        print(f"  • High Paying (≥10 LPA): {high_paying} job categories")
        print(f"  • Mid Paying (5-10 LPA): {mid_paying} job categories")  
        print(f"  • Entry Level (<5 LPA): {entry_paying} job categories")
        print(f"  • Total job categories: {total_categories}")
        print(f"  • Total jobs processed: {processed_jobs}")

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
