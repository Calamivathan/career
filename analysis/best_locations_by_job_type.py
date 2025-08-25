#!/usr/bin/env python3
"""
Analysis: Best Locations by Job Type
Analyzes the best locations for different types of jobs based on job count, salary, and opportunities
"""

import pymysql
import json
import re
from collections import defaultdict
from statistics import mean

def extract_salary_value(salary_text):
    """Extract numeric salary value from text"""
    if not salary_text:
        return None

    salary_str = str(salary_text).lower().replace(',', '').replace(' ', '')
    numbers = re.findall(r'\d+(?:\.\d+)?', salary_str)
    if not numbers:
        return None

    salary_value = float(numbers[0])

    if 'lpa' in salary_str or 'per annum' in salary_str:
        return salary_value * 100000
    elif 'crore' in salary_str:
        return salary_value * 10000000
    elif 'lakh' in salary_str:
        return salary_value * 100000
    elif 'k' in salary_str and salary_value < 1000:
        return salary_value * 1000
    elif salary_value > 1000000:
        return salary_value
    else:
        return salary_value * 100000

def normalize_job_type(title):
    """Normalize job titles into categories"""
    if not title:
        return "Unknown"

    title_lower = title.lower()

    if any(keyword in title_lower for keyword in ['software engineer', 'developer', 'programmer', 'backend', 'frontend']):
        return 'Software Development'
    elif any(keyword in title_lower for keyword in ['data engineer', 'data scientist', 'data analyst']):
        return 'Data Science & Analytics'
    elif any(keyword in title_lower for keyword in ['ai engineer', 'ml engineer', 'machine learning']):
        return 'AI/Machine Learning'
    elif any(keyword in title_lower for keyword in ['qa engineer', 'test engineer', 'quality']):
        return 'Quality Assurance'
    elif any(keyword in title_lower for keyword in ['manager', 'lead', 'head', 'director']):
        return 'Management & Leadership'
    elif any(keyword in title_lower for keyword in ['consultant', 'advisor']):
        return 'Consulting'
    elif any(keyword in title_lower for keyword in ['designer', 'ui', 'ux']):
        return 'Design & UX'
    elif any(keyword in title_lower for keyword in ['marketing', 'sales']):
        return 'Marketing & Sales'
    elif any(keyword in title_lower for keyword in ['intern', 'trainee']):
        return 'Internships'
    else:
        return 'Other'

def normalize_location(location):
    """Normalize location names"""
    if not location:
        return "Unknown"

    location_lower = location.lower().strip()

    # Major city mappings
    city_mappings = {
        'bangalore': 'Bangalore',
        'bengaluru': 'Bangalore', 
        'mumbai': 'Mumbai',
        'pune': 'Pune',
        'delhi': 'Delhi',
        'new delhi': 'Delhi',
        'gurgaon': 'Gurgaon',
        'gurugram': 'Gurgaon',
        'hyderabad': 'Hyderabad',
        'chennai': 'Chennai',
        'kolkata': 'Kolkata',
        'ahmedabad': 'Ahmedabad',
        'noida': 'Noida',
        'kochi': 'Kochi',
        'cochin': 'Kochi',
        'thiruvananthapuram': 'Thiruvananthapuram',
        'coimbatore': 'Coimbatore',
        'indore': 'Indore',
        'jaipur': 'Jaipur',
        'lucknow': 'Lucknow',
        'chandigarh': 'Chandigarh'
    }

    for key, value in city_mappings.items():
        if key in location_lower:
            return value

    # Return original if not found in mappings
    return location.title()

def get_related_jobs(connection, job_type, location, limit=5):
    """Get related available jobs for this job type and location"""
    try:
        cursor = connection.cursor()

        query = """
        SELECT title, company, location, salary, job_id, openings
        FROM jobs_latest 
        WHERE title LIKE %s AND location LIKE %s
        ORDER BY CAST(REGEXP_REPLACE(REGEXP_REPLACE(salary, '[^0-9.]', ''), '^0+', '') AS DECIMAL(15,2)) DESC
        LIMIT %s
        """

        job_pattern = f"%{job_type.split()[0].lower()}%"
        location_pattern = f"%{location}%"
        cursor.execute(query, (job_pattern, location_pattern, limit))

        jobs = cursor.fetchall()
        related_jobs = []

        for job in jobs:
            job_info = {
                'title': job['title'],
                'company': job['company'], 
                'location': job['location'],
                'salary': job['salary'],
                'job_id': job['job_id'],
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

        print("🔍 Fetching job data for location analysis...")

        # Fetch jobs with location and other relevant data
        query = """
        SELECT title, location, salary, openings, company
        FROM jobs_complete 
        WHERE location IS NOT NULL 
        AND location != ''
        """

        cursor.execute(query)
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found with location data")
            return False

        print(f"📊 Processing {len(jobs)} jobs with location information...")

        # Group jobs by job type and location
        location_job_data = defaultdict(lambda: defaultdict(lambda: {
            'job_count': 0,
            'total_openings': 0,
            'salaries': [],
            'companies': set()
        }))

        processed_jobs = 0

        for job in jobs:
            job_type = normalize_job_type(job['title'])
            location = normalize_location(job['location'])

            if job_type != "Unknown" and location != "Unknown":
                location_job_data[job_type][location]['job_count'] += 1

                # Add openings
                try:
                    openings = int(job['openings']) if job['openings'] else 1
                    location_job_data[job_type][location]['total_openings'] += openings
                except (ValueError, TypeError):
                    location_job_data[job_type][location]['total_openings'] += 1

                # Add salary if available
                salary_value = extract_salary_value(job['salary'])
                if salary_value and salary_value > 0:
                    location_job_data[job_type][location]['salaries'].append(salary_value)

                # Add company
                if job['company']:
                    location_job_data[job_type][location]['companies'].add(job['company'])

                processed_jobs += 1

        print(f"✅ Successfully processed {processed_jobs} jobs")

        print("💾 Clearing previous analysis results...")

        # Clear previous results
        cursor.execute("DELETE FROM analysis_best_locations")

        print("📈 Analyzing best locations for each job type...")

        # Analyze and store results
        results_stored = 0

        for job_type, locations in location_job_data.items():
            # Filter locations with meaningful data (at least 3 jobs)
            valid_locations = {loc: data for loc, data in locations.items() if data['job_count'] >= 3}

            if not valid_locations:
                continue

            # Sort locations by job count and average salary
            location_scores = []

            for location, data in valid_locations.items():
                avg_salary = mean(data['salaries']) if data['salaries'] else 0

                # Calculate a composite score (weighted by job count and salary)
                score = data['job_count'] * 0.6 + (avg_salary / 100000) * 0.4

                location_scores.append({
                    'location': location,
                    'job_count': data['job_count'],
                    'total_openings': data['total_openings'],
                    'avg_salary': avg_salary,
                    'company_count': len(data['companies']),
                    'score': score
                })

            # Sort by score (descending)
            location_scores.sort(key=lambda x: x['score'], reverse=True)

            # Store top locations for this job type
            for location_data in location_scores[:10]:  # Top 10 locations per job type
                related_jobs = get_related_jobs(connection, job_type, location_data['location'])

                insert_query = """
                INSERT INTO analysis_best_locations 
                (job_type, location, job_count, avg_salary, total_openings, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                """

                cursor.execute(insert_query, (
                    job_type,
                    location_data['location'],
                    location_data['job_count'],
                    round(location_data['avg_salary'], 2) if location_data['avg_salary'] > 0 else 0,
                    location_data['total_openings'],
                    related_jobs
                ))

                results_stored += 1

        print(f"✅ Analysis completed! Stored {results_stored} location-job type combinations")

        # Print summary
        print("\n🌍 Top Locations by Job Type:")

        for job_type in ['Software Development', 'Data Science & Analytics', 'AI/Machine Learning']:
            if job_type in location_job_data:
                print(f"\n{job_type}:")
                valid_locations = {loc: data for loc, data in location_job_data[job_type].items() if data['job_count'] >= 3}
                sorted_locations = sorted(valid_locations.items(), key=lambda x: x[1]['job_count'], reverse=True)[:5]

                for location, data in sorted_locations:
                    avg_salary_lpa = mean(data['salaries']) / 100000 if data['salaries'] else 0
                    print(f"  • {location}: {data['job_count']} jobs, {avg_salary_lpa:.1f} LPA avg")

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
