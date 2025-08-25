# Create remaining analysis modules (7-15)

# Analysis 7: Company Hiring Trends
analysis_7_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Company Hiring Trends
Analyzes which companies are hiring most and their patterns
\"\"\"

import pymysql
import json
from collections import defaultdict, Counter
from statistics import mean
import re

def extract_salary_value(salary_text):
    if not salary_text:
        return None
    salary_str = str(salary_text).lower().replace(',', '').replace(' ', '')
    numbers = re.findall(r'\\d+(?:\\.\\d+)?', salary_str)
    if not numbers:
        return None
    salary_value = float(numbers[0])
    if 'lpa' in salary_str:
        return salary_value * 100000
    return salary_value * 100000 if salary_value < 1000 else salary_value

def normalize_job_title(title):
    if not title:
        return "Other"
    title_lower = title.lower()
    if 'engineer' in title_lower or 'developer' in title_lower:
        return 'Engineering'
    elif 'analyst' in title_lower:
        return 'Analytics'
    elif 'manager' in title_lower:
        return 'Management'
    else:
        return 'Other'

def get_related_jobs(connection, company, limit=5):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT title, company, location, salary, job_id FROM jobs_latest WHERE company = %s LIMIT %s\"\"\"
        cursor.execute(query, (company, limit))
        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id']} for job in jobs]
        return json.dumps(related_jobs)
    except Exception as e:
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT company, title, salary, openings FROM jobs_complete WHERE company IS NOT NULL AND company != ''\"\"\"
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        if not jobs:
            return False
        
        company_data = defaultdict(lambda: {'total_jobs': 0, 'total_openings': 0, 'salaries': [], 'job_types': []})
        
        for job in jobs:
            company = job['company'].strip()
            if len(company) > 2:  # Filter out very short company names
                company_data[company]['total_jobs'] += 1
                
                try:
                    openings = int(job['openings']) if job['openings'] else 1
                    company_data[company]['total_openings'] += openings
                except:
                    company_data[company]['total_openings'] += 1
                
                salary_value = extract_salary_value(job['salary'])
                if salary_value:
                    company_data[company]['salaries'].append(salary_value)
                
                job_type = normalize_job_title(job['title'])
                company_data[company]['job_types'].append(job_type)
        
        cursor.execute("DELETE FROM analysis_company_hiring_trends")
        
        # Filter companies with meaningful data
        significant_companies = {k: v for k, v in company_data.items() if v['total_jobs'] >= 3}
        company_list = sorted(significant_companies.items(), key=lambda x: x[1]['total_jobs'], reverse=True)[:50]
        
        results_stored = 0
        for company, data in company_list:
            avg_salary = mean(data['salaries']) if data['salaries'] else 0
            top_job_types = [jt for jt, count in Counter(data['job_types']).most_common(3)]
            hiring_trend = "High" if data['total_jobs'] >= 20 else "Moderate" if data['total_jobs'] >= 10 else "Low"
            related_jobs = get_related_jobs(connection, company)
            
            insert_query = \"\"\"
            INSERT INTO analysis_company_hiring_trends 
            (company, total_jobs, total_openings, avg_salary, top_job_types, hiring_trend, related_jobs)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            \"\"\"
            
            cursor.execute(insert_query, (
                company, data['total_jobs'], data['total_openings'], round(avg_salary, 2),
                json.dumps(top_job_types), hiring_trend, related_jobs
            ))
            results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} company records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Analysis 8: Salary by Experience Trends  
analysis_8_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Salary by Experience Trends
Analyzes salary progression with experience levels
\"\"\"

import pymysql
import json
import re
from collections import defaultdict
from statistics import mean, median

def extract_salary_value(salary_text):
    if not salary_text:
        return None
    salary_str = str(salary_text).lower().replace(',', '').replace(' ', '')
    numbers = re.findall(r'\\d+(?:\\.\\d+)?', salary_str)
    if not numbers:
        return None
    salary_value = float(numbers[0])
    if 'lpa' in salary_str:
        return salary_value * 100000
    return salary_value * 100000 if salary_value < 1000 else salary_value

def categorize_experience_range(min_exp, max_exp):
    try:
        min_val = float(min_exp) if min_exp else 0
        max_val = float(max_exp) if max_exp else min_val
        avg_exp = (min_val + max_val) / 2
        
        if avg_exp <= 1:
            return '0-1 years'
        elif avg_exp <= 3:
            return '2-3 years'
        elif avg_exp <= 5:
            return '4-5 years'
        elif avg_exp <= 8:
            return '6-8 years'
        elif avg_exp <= 12:
            return '9-12 years'
        else:
            return '12+ years'
    except:
        return 'Unknown'

def get_related_jobs(connection, exp_range, limit=5):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT title, company, location, salary, job_id FROM jobs_latest LIMIT %s\"\"\"
        cursor.execute(query, (limit,))
        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id']} for job in jobs]
        return json.dumps(related_jobs)
    except:
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT minimum_experience, maximum_experience, salary FROM jobs_complete WHERE salary IS NOT NULL AND salary != ''\"\"\"
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        if not jobs:
            return False
        
        exp_salary_data = defaultdict(list)
        
        for job in jobs:
            exp_range = categorize_experience_range(job.get('minimum_experience'), job.get('maximum_experience'))
            if exp_range != 'Unknown':
                salary_value = extract_salary_value(job['salary'])
                if salary_value and salary_value > 0:
                    exp_salary_data[exp_range].append(salary_value)
        
        cursor.execute("DELETE FROM analysis_salary_experience_trends")
        
        # Calculate growth rates
        sorted_ranges = ['0-1 years', '2-3 years', '4-5 years', '6-8 years', '9-12 years', '12+ years']
        prev_avg = None
        results_stored = 0
        
        for exp_range in sorted_ranges:
            if exp_range in exp_salary_data and len(exp_salary_data[exp_range]) >= 3:
                salaries = exp_salary_data[exp_range]
                avg_salary = mean(salaries)
                median_salary = median(salaries)
                
                growth_rate = 0
                if prev_avg:
                    growth_rate = ((avg_salary - prev_avg) / prev_avg) * 100
                
                related_jobs = get_related_jobs(connection, exp_range)
                
                insert_query = \"\"\"
                INSERT INTO analysis_salary_experience_trends 
                (experience_range, avg_salary, median_salary, salary_growth_rate, job_count, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                \"\"\"
                
                cursor.execute(insert_query, (
                    exp_range, round(avg_salary, 2), round(median_salary, 2),
                    round(growth_rate, 2), len(salaries), related_jobs
                ))
                
                prev_avg = avg_salary
                results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} experience-salary records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Save these files
with open('analysis/company_hiring_trends.py', 'w') as f:
    f.write(analysis_7_content)

with open('analysis/salary_by_experience_trends.py', 'w') as f:
    f.write(analysis_8_content)

print("✓ Created analysis/company_hiring_trends.py")
print("✓ Created analysis/salary_by_experience_trends.py")