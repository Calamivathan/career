# Create the remaining analysis modules (9-15)

# Analysis 9: Government vs Private Analysis
analysis_9_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Government vs Private Sector Analysis
Compares job opportunities in government vs private sector
\"\"\"

import pymysql
import json
import re
from collections import defaultdict, Counter
from statistics import mean

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
    elif 'consultant' in title_lower:
        return 'Consulting'
    else:
        return 'Other'

def get_related_jobs(connection, sector, limit=5):
    try:
        cursor = connection.cursor()
        if sector == 'Government':
            query = \"\"\"SELECT title, company, location, salary, job_id FROM jobs_latest WHERE is_govt = '1' LIMIT %s\"\"\"
        else:
            query = \"\"\"SELECT title, company, location, salary, job_id FROM jobs_latest WHERE is_govt = '0' OR is_govt IS NULL LIMIT %s\"\"\"
        
        cursor.execute(query, (limit,))
        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id']} for job in jobs]
        return json.dumps(related_jobs)
    except:
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT title, salary, openings, is_govt FROM jobs_complete\"\"\"
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        if not jobs:
            return False
        
        sector_data = {'Government': defaultdict(int), 'Private': defaultdict(int)}
        sector_salaries = {'Government': [], 'Private': []}
        sector_job_types = {'Government': [], 'Private': []}
        sector_openings = {'Government': 0, 'Private': 0}
        
        for job in jobs:
            is_govt = job.get('is_govt')
            sector = 'Government' if str(is_govt) == '1' else 'Private'
            
            sector_data[sector]['job_count'] += 1
            
            try:
                openings = int(job['openings']) if job['openings'] else 1
                sector_openings[sector] += openings
            except:
                sector_openings[sector] += 1
            
            salary_value = extract_salary_value(job.get('salary'))
            if salary_value:
                sector_salaries[sector].append(salary_value)
            
            job_type = normalize_job_title(job.get('title'))
            sector_job_types[sector].append(job_type)
        
        cursor.execute("DELETE FROM analysis_govt_vs_private")
        results_stored = 0
        
        for sector in ['Government', 'Private']:
            if sector_data[sector]['job_count'] > 0:
                avg_salary = mean(sector_salaries[sector]) if sector_salaries[sector] else 0
                top_job_types = [jt for jt, count in Counter(sector_job_types[sector]).most_common(5)]
                related_jobs = get_related_jobs(connection, sector)
                
                insert_query = \"\"\"
                INSERT INTO analysis_govt_vs_private 
                (sector, job_count, avg_salary, top_job_types, total_openings, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                \"\"\"
                
                cursor.execute(insert_query, (
                    sector, sector_data[sector]['job_count'], round(avg_salary, 2),
                    json.dumps(top_job_types), sector_openings[sector], related_jobs
                ))
                results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} sector records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Analysis 10: Job Duration Analysis
analysis_10_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Job Duration Analysis
Analyzes job opportunities by contract duration
\"\"\"

import pymysql
import json
import re
from collections import defaultdict, Counter
from statistics import mean

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

def categorize_duration(duration_text, position_type):
    if not duration_text and not position_type:
        return 'Permanent'
    
    duration_str = str(duration_text).lower() if duration_text else ""
    position_str = str(position_type).lower() if position_type else ""
    
    if any(word in duration_str for word in ['permanent', 'full time']) or 'full time' in position_str:
        return 'Permanent'
    elif any(word in duration_str for word in ['6 months', '6month', 'six months']):
        return '6 Months Contract'
    elif any(word in duration_str for word in ['3 months', '3month', 'three months']):
        return '3 Months Contract'
    elif any(word in duration_str for word in ['1 year', '12 months', 'one year']):
        return '1 Year Contract'
    elif any(word in duration_str for word in ['intern', 'internship']) or 'intern' in position_str:
        return 'Internship'
    elif 'contract' in duration_str or 'contract' in position_str:
        return 'Contract (Other)'
    else:
        return 'Permanent'

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

def get_related_jobs(connection, duration_category, limit=5):
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
        query = \"\"\"SELECT title, duration, position_type, salary FROM jobs_complete\"\"\"
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        if not jobs:
            return False
        
        duration_data = defaultdict(lambda: {'job_count': 0, 'salaries': [], 'job_types': []})
        
        for job in jobs:
            duration_category = categorize_duration(job.get('duration'), job.get('position_type'))
            duration_data[duration_category]['job_count'] += 1
            
            salary_value = extract_salary_value(job.get('salary'))
            if salary_value:
                duration_data[duration_category]['salaries'].append(salary_value)
            
            job_type = normalize_job_title(job.get('title'))
            duration_data[duration_category]['job_types'].append(job_type)
        
        cursor.execute("DELETE FROM analysis_job_duration")
        
        total_jobs = sum(data['job_count'] for data in duration_data.values())
        results_stored = 0
        
        for duration_category, data in duration_data.items():
            if data['job_count'] > 0:
                percentage = (data['job_count'] / total_jobs) * 100
                avg_salary = mean(data['salaries']) if data['salaries'] else 0
                popular_job_types = [jt for jt, count in Counter(data['job_types']).most_common(3)]
                related_jobs = get_related_jobs(connection, duration_category)
                
                insert_query = \"\"\"
                INSERT INTO analysis_job_duration 
                (duration_category, job_count, percentage, avg_salary, popular_job_types, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                \"\"\"
                
                cursor.execute(insert_query, (
                    duration_category, data['job_count'], round(percentage, 2),
                    round(avg_salary, 2), json.dumps(popular_job_types), related_jobs
                ))
                results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} duration category records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Save these files
with open('analysis/govt_vs_private_analysis.py', 'w') as f:
    f.write(analysis_9_content)

with open('analysis/job_duration_analysis.py', 'w') as f:
    f.write(analysis_10_content)

print("✓ Created analysis/govt_vs_private_analysis.py")
print("✓ Created analysis/job_duration_analysis.py")