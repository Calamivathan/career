# Create the final batch of analysis modules (11-15)

# Analysis 11: Skills Demand by Location
analysis_11_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Skills Demand by Location
Analyzes which skills are in demand in different locations
\"\"\"

import pymysql
import json
import re
from collections import defaultdict, Counter
from statistics import mean

def extract_skills_from_text(text):
    if not text:
        return []
    skills = []
    parts = re.split(r'[,;|]', str(text))
    for part in parts:
        skill = part.strip()
        if skill and len(skill) > 1:
            skills.append(skill.title())
    return skills

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

def normalize_location(location):
    if not location:
        return "Unknown"
    location_lower = location.lower().strip()
    city_mappings = {
        'bangalore': 'Bangalore', 'bengaluru': 'Bangalore', 
        'mumbai': 'Mumbai', 'pune': 'Pune', 'delhi': 'Delhi',
        'new delhi': 'Delhi', 'gurgaon': 'Gurgaon', 'gurugram': 'Gurgaon',
        'hyderabad': 'Hyderabad', 'chennai': 'Chennai', 'kolkata': 'Kolkata'
    }
    for key, value in city_mappings.items():
        if key in location_lower:
            return value
    return location.title()

def get_related_jobs(connection, location, skill, limit=5):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT title, company, location, salary, job_id FROM jobs_latest 
                   WHERE location LIKE %s AND (tags_and_skills LIKE %s OR job_description LIKE %s) LIMIT %s\"\"\"
        location_pattern = f"%{location}%"
        skill_pattern = f"%{skill}%"
        cursor.execute(query, (location_pattern, skill_pattern, skill_pattern, limit))
        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id']} for job in jobs]
        return json.dumps(related_jobs)
    except:
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT location, tags_and_skills, job_description, salary FROM jobs_complete 
                   WHERE location IS NOT NULL AND location != '' AND tags_and_skills IS NOT NULL\"\"\"
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        if not jobs:
            return False
        
        location_skill_data = defaultdict(lambda: defaultdict(lambda: {'frequency': 0, 'job_count': 0, 'salaries': []}))
        
        for job in jobs:
            location = normalize_location(job['location'])
            if location != "Unknown":
                skills = extract_skills_from_text(job['tags_and_skills'])
                if job.get('job_description'):
                    skills.extend(extract_skills_from_text(job['job_description']))
                
                salary_value = extract_salary_value(job.get('salary'))
                
                for skill in skills:
                    if len(skill) > 2:  # Filter out very short skills
                        location_skill_data[location][skill]['frequency'] += 1
                        if salary_value:
                            location_skill_data[location][skill]['salaries'].append(salary_value)
                        location_skill_data[location][skill]['job_count'] += 1
        
        cursor.execute("DELETE FROM analysis_skills_by_location")
        results_stored = 0
        
        for location, skills_data in location_skill_data.items():
            # Only consider locations with meaningful data
            if len(skills_data) >= 10:
                # Get top skills for this location
                top_skills = sorted(skills_data.items(), key=lambda x: x[1]['frequency'], reverse=True)[:20]
                
                for skill, data in top_skills:
                    if data['frequency'] >= 3:  # Only skills mentioned at least 3 times
                        avg_salary = mean(data['salaries']) if data['salaries'] else 0
                        related_jobs = get_related_jobs(connection, location, skill)
                        
                        insert_query = \"\"\"
                        INSERT INTO analysis_skills_by_location 
                        (location, skill, frequency, job_count, avg_salary, related_jobs)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        \"\"\"
                        
                        cursor.execute(insert_query, (
                            location, skill, data['frequency'], data['job_count'],
                            round(avg_salary, 2), related_jobs
                        ))
                        results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} location-skill records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Analysis 12: Most Competitive Jobs
analysis_12_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Most Competitive Jobs
Analyzes jobs with highest competition ratios (applications per opening)
\"\"\"

import pymysql
import json
from collections import defaultdict

def normalize_job_title(title):
    if not title:
        return "Unknown"
    title_lower = title.lower()
    if any(keyword in title_lower for keyword in ['engineer', 'developer']):
        if 'data' in title_lower:
            return 'Data Engineer/Developer'
        elif 'software' in title_lower:
            return 'Software Engineer/Developer'
        elif 'ai' in title_lower or 'ml' in title_lower:
            return 'AI/ML Engineer'
        else:
            return 'Engineer/Developer'
    elif 'analyst' in title_lower:
        return 'Data Analyst' if 'data' in title_lower else 'Business Analyst'
    elif 'manager' in title_lower:
        return 'Management'
    elif 'scientist' in title_lower:
        return 'Data Scientist'
    else:
        return title.title()

def get_competition_level(ratio):
    if ratio >= 100:
        return 'Extremely High'
    elif ratio >= 50:
        return 'Very High'
    elif ratio >= 20:
        return 'High'
    elif ratio >= 10:
        return 'Moderate'
    else:
        return 'Low'

def get_related_jobs(connection, job_title, limit=5):
    try:
        cursor = connection.cursor()
        search_pattern = f"%{job_title.split('/')[0].lower()}%"
        query = \"\"\"SELECT title, company, location, salary, job_id, apply_count, openings FROM jobs_latest 
                   WHERE title LIKE %s ORDER BY CAST(apply_count AS UNSIGNED) DESC LIMIT %s\"\"\"
        cursor.execute(query, (search_pattern, limit))
        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id'], 'apply_count': job.get('apply_count', 0), 'openings': job.get('openings', 1)} for job in jobs]
        return json.dumps(related_jobs)
    except:
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT title, apply_count, openings FROM jobs_complete 
                   WHERE apply_count IS NOT NULL AND apply_count > 0 AND openings IS NOT NULL AND openings > 0\"\"\"
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        if not jobs:
            return False
        
        job_competition_data = defaultdict(lambda: {'total_applications': 0, 'total_openings': 0, 'job_count': 0})
        
        for job in jobs:
            try:
                apply_count = int(job['apply_count'])
                openings = int(job['openings'])
                
                if apply_count > 0 and openings > 0:
                    normalized_title = normalize_job_title(job['title'])
                    job_competition_data[normalized_title]['total_applications'] += apply_count
                    job_competition_data[normalized_title]['total_openings'] += openings
                    job_competition_data[normalized_title]['job_count'] += 1
            except:
                continue
        
        cursor.execute("DELETE FROM analysis_competitive_jobs")
        results_stored = 0
        
        competition_analysis = []
        for job_title, data in job_competition_data.items():
            if data['job_count'] >= 3:  # Only meaningful data
                avg_applications_per_opening = data['total_applications'] / data['total_openings']
                competition_level = get_competition_level(avg_applications_per_opening)
                
                competition_analysis.append({
                    'job_title': job_title,
                    'avg_applications_per_opening': avg_applications_per_opening,
                    'total_applications': data['total_applications'],
                    'total_openings': data['total_openings'],
                    'competition_level': competition_level
                })
        
        # Sort by competition ratio
        competition_analysis.sort(key=lambda x: x['avg_applications_per_opening'], reverse=True)
        
        for comp_data in competition_analysis:
            related_jobs = get_related_jobs(connection, comp_data['job_title'])
            
            insert_query = \"\"\"
            INSERT INTO analysis_competitive_jobs 
            (job_title, avg_applications_per_opening, total_applications, total_openings, competition_level, related_jobs)
            VALUES (%s, %s, %s, %s, %s, %s)
            \"\"\"
            
            cursor.execute(insert_query, (
                comp_data['job_title'], round(comp_data['avg_applications_per_opening'], 2),
                comp_data['total_applications'], comp_data['total_openings'],
                comp_data['competition_level'], related_jobs
            ))
            results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} competitive job records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Save these files
with open('analysis/skills_demand_by_location.py', 'w') as f:
    f.write(analysis_11_content)

with open('analysis/most_competitive_jobs.py', 'w') as f:
    f.write(analysis_12_content)

print("✓ Created analysis/skills_demand_by_location.py")
print("✓ Created analysis/most_competitive_jobs.py")