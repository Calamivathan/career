# Create the final 3 analysis modules (13-15)

# Analysis 13: Emerging Job Titles
analysis_13_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Emerging Job Titles
Analyzes new and trending job titles that are gaining popularity
\"\"\"

import pymysql
import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta
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

def clean_job_title(title):
    \"\"\"Clean and normalize job titles\"\"\"
    if not title:
        return None
    
    # Remove common prefixes and suffixes that don't add meaning
    title_clean = re.sub(r'^(senior|junior|sr|jr)\s+', '', title.strip(), flags=re.IGNORECASE)
    title_clean = re.sub(r'\s+(i{1,3}|1|2|3)$', '', title_clean, flags=re.IGNORECASE)
    
    return title_clean.strip().title() if len(title_clean) > 3 else None

def get_related_jobs(connection, job_title, limit=5):
    try:
        cursor = connection.cursor()
        query = \"\"\"SELECT title, company, location, salary, job_id FROM jobs_latest 
                   WHERE title LIKE %s LIMIT %s\"\"\"
        search_pattern = f"%{job_title.split()[0].lower()}%"
        cursor.execute(query, (search_pattern, limit))
        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id']} for job in jobs]
        return json.dumps(related_jobs)
    except:
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        
        # Get current date and calculate 6 months ago
        now = datetime.now()
        six_months_ago = now - timedelta(days=180)
        
        # Fetch recent jobs
        recent_query = \"\"\"SELECT title, tags_and_skills, salary, created_at FROM jobs_complete 
                         WHERE created_at >= %s AND title IS NOT NULL\"\"\"
        cursor.execute(recent_query, (six_months_ago.strftime('%Y-%m-%d'),))
        recent_jobs = cursor.fetchall()
        
        # Fetch older jobs for comparison
        older_query = \"\"\"SELECT title, tags_and_skills, salary, created_at FROM jobs_complete 
                        WHERE created_at < %s AND title IS NOT NULL\"\"\"
        cursor.execute(older_query, (six_months_ago.strftime('%Y-%m-%d'),))
        older_jobs = cursor.fetchall()
        
        if not recent_jobs:
            print("No recent jobs found")
            return False
        
        # Count job titles in each period
        recent_titles = Counter()
        older_titles = Counter()
        title_salaries = defaultdict(list)
        title_skills = defaultdict(list)
        
        for job in recent_jobs:
            clean_title = clean_job_title(job['title'])
            if clean_title:
                recent_titles[clean_title] += 1
                
                salary_value = extract_salary_value(job.get('salary'))
                if salary_value:
                    title_salaries[clean_title].append(salary_value)
                
                skills = extract_skills_from_text(job.get('tags_and_skills'))
                title_skills[clean_title].extend(skills)
        
        for job in older_jobs:
            clean_title = clean_job_title(job['title'])
            if clean_title:
                older_titles[clean_title] += 1
        
        cursor.execute("DELETE FROM analysis_emerging_job_titles")
        results_stored = 0
        
        # Identify emerging titles
        emerging_titles = []
        
        for title, recent_count in recent_titles.items():
            if recent_count >= 5:  # Only consider titles with meaningful recent activity
                older_count = older_titles.get(title, 0)
                
                # Calculate growth rate
                if older_count == 0:
                    growth_rate = 100.0 if recent_count > 0 else 0.0
                else:
                    growth_rate = ((recent_count - older_count) / older_count) * 100
                
                # Focus on titles with high growth or completely new titles
                if growth_rate >= 50 or older_count == 0:
                    avg_salary = mean(title_salaries[title]) if title_salaries[title] else 0
                    top_skills = [skill for skill, count in Counter(title_skills[title]).most_common(5)]
                    
                    emerging_titles.append({
                        'title': title,
                        'recent_count': recent_count,
                        'growth_rate': growth_rate,
                        'avg_salary': avg_salary,
                        'key_skills': top_skills
                    })
        
        # Sort by growth rate and recent count
        emerging_titles.sort(key=lambda x: (x['growth_rate'], x['recent_count']), reverse=True)
        
        # Store results
        for title_data in emerging_titles[:30]:  # Top 30 emerging titles
            related_jobs = get_related_jobs(connection, title_data['title'])
            
            insert_query = \"\"\"
            INSERT INTO analysis_emerging_job_titles 
            (job_title, recent_count, growth_rate, avg_salary, key_skills, related_jobs)
            VALUES (%s, %s, %s, %s, %s, %s)
            \"\"\"
            
            cursor.execute(insert_query, (
                title_data['title'], title_data['recent_count'],
                round(title_data['growth_rate'], 2), round(title_data['avg_salary'], 2),
                json.dumps(title_data['key_skills']), related_jobs
            ))
            results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} emerging job title records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Analysis 14: Experience Requirements Trends
analysis_14_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Experience Requirements Trends
Analyzes how experience requirements are changing across job categories
\"\"\"

import pymysql
import json
from collections import defaultdict
from statistics import mean
from datetime import datetime, timedelta

def normalize_job_category(title):
    if not title:
        return "Other"
    title_lower = title.lower()
    
    if any(keyword in title_lower for keyword in ['software engineer', 'developer', 'programmer']):
        return 'Software Development'
    elif any(keyword in title_lower for keyword in ['data engineer', 'data scientist', 'data analyst']):
        return 'Data Science'
    elif any(keyword in title_lower for keyword in ['ai', 'ml', 'machine learning']):
        return 'AI/Machine Learning'
    elif any(keyword in title_lower for keyword in ['product manager', 'project manager']):
        return 'Product Management'
    elif any(keyword in title_lower for keyword in ['qa', 'test', 'quality']):
        return 'Quality Assurance'
    elif any(keyword in title_lower for keyword in ['designer', 'ui', 'ux']):
        return 'Design'
    elif any(keyword in title_lower for keyword in ['marketing', 'sales']):
        return 'Marketing/Sales'
    elif any(keyword in title_lower for keyword in ['consultant', 'analyst']):
        return 'Consulting/Analysis'
    else:
        return 'Other'

def get_related_jobs(connection, job_category, limit=5):
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
        
        # Get current date and calculate periods
        now = datetime.now()
        six_months_ago = now - timedelta(days=180)
        
        # Fetch recent jobs
        recent_query = \"\"\"SELECT title, minimum_experience, maximum_experience FROM jobs_complete 
                         WHERE created_at >= %s AND title IS NOT NULL\"\"\"
        cursor.execute(recent_query, (six_months_ago.strftime('%Y-%m-%d'),))
        recent_jobs = cursor.fetchall()
        
        # Fetch older jobs
        older_query = \"\"\"SELECT title, minimum_experience, maximum_experience FROM jobs_complete 
                        WHERE created_at < %s AND title IS NOT NULL\"\"\"
        cursor.execute(older_query, (six_months_ago.strftime('%Y-%m-%d'),))
        older_jobs = cursor.fetchall()
        
        if not recent_jobs and not older_jobs:
            return False
        
        def process_jobs(jobs):
            category_experience = defaultdict(lambda: {'min_exp': [], 'max_exp': [], 'job_count': 0})
            
            for job in jobs:
                try:
                    category = normalize_job_category(job['title'])
                    min_exp = float(job['minimum_experience']) if job['minimum_experience'] else 0
                    max_exp = float(job['maximum_experience']) if job['maximum_experience'] else min_exp
                    
                    category_experience[category]['min_exp'].append(min_exp)
                    category_experience[category]['max_exp'].append(max_exp)
                    category_experience[category]['job_count'] += 1
                except:
                    continue
            
            return category_experience
        
        recent_data = process_jobs(recent_jobs)
        older_data = process_jobs(older_jobs)
        
        cursor.execute("DELETE FROM analysis_experience_requirements")
        results_stored = 0
        
        # Analyze trends for each category
        for category in set(list(recent_data.keys()) + list(older_data.keys())):
            recent_cat_data = recent_data.get(category, {'min_exp': [], 'max_exp': [], 'job_count': 0})
            older_cat_data = older_data.get(category, {'min_exp': [], 'max_exp': [], 'job_count': 0})
            
            if recent_cat_data['job_count'] >= 3:  # Only meaningful data
                avg_min_recent = mean(recent_cat_data['min_exp']) if recent_cat_data['min_exp'] else 0
                avg_max_recent = mean(recent_cat_data['max_exp']) if recent_cat_data['max_exp'] else 0
                
                avg_min_older = mean(older_cat_data['min_exp']) if older_cat_data['min_exp'] else avg_min_recent
                avg_max_older = mean(older_cat_data['max_exp']) if older_cat_data['max_exp'] else avg_max_recent
                
                # Determine trend
                if avg_min_recent > avg_min_older:
                    trend = 'Increasing'
                elif avg_min_recent < avg_min_older:
                    trend = 'Decreasing'
                else:
                    trend = 'Stable'
                
                related_jobs = get_related_jobs(connection, category)
                
                insert_query = \"\"\"
                INSERT INTO analysis_experience_requirements 
                (job_category, avg_min_experience, avg_max_experience, experience_trend, job_count, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                \"\"\"
                
                cursor.execute(insert_query, (
                    category, round(avg_min_recent, 1), round(avg_max_recent, 1),
                    trend, recent_cat_data['job_count'], related_jobs
                ))
                results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} experience trend records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Analysis 15: Skills Correlation Analysis
analysis_15_content = """#!/usr/bin/env python3
\"\"\"
Analysis: Skills Correlation Analysis
Analyzes which skills commonly appear together in job requirements
\"\"\"

import pymysql
import json
import re
from collections import defaultdict, Counter
from itertools import combinations
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

def normalize_job_type(title):
    if not title:
        return "Other"
    title_lower = title.lower()
    
    if 'engineer' in title_lower or 'developer' in title_lower:
        return 'Engineering'
    elif 'analyst' in title_lower:
        return 'Analytics'
    elif 'scientist' in title_lower:
        return 'Data Science'
    elif 'manager' in title_lower:
        return 'Management'
    else:
        return 'Other'

def get_related_jobs(connection, skill_combo, limit=5):
    try:
        cursor = connection.cursor()
        skills = skill_combo.split(' + ')
        if len(skills) >= 2:
            query = \"\"\"SELECT title, company, location, salary, job_id FROM jobs_latest 
                       WHERE tags_and_skills LIKE %s AND tags_and_skills LIKE %s LIMIT %s\"\"\"
            pattern1 = f"%{skills[0]}%"
            pattern2 = f"%{skills[1]}%"
            cursor.execute(query, (pattern1, pattern2, limit))
        else:
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
        query = \"\"\"SELECT title, tags_and_skills, job_description, salary FROM jobs_complete 
                   WHERE tags_and_skills IS NOT NULL AND tags_and_skills != ''\"\"\"
        cursor.execute(query)
        jobs = cursor.fetchall()
        
        if not jobs:
            return False
        
        # Extract skills from each job
        job_skills_data = []
        skill_counts = Counter()
        
        for job in jobs:
            skills = extract_skills_from_text(job['tags_and_skills'])
            if job.get('job_description'):
                skills.extend(extract_skills_from_text(job['job_description']))
            
            # Filter out duplicates and very short skills
            skills = list(set([skill for skill in skills if len(skill) > 2]))
            
            if len(skills) >= 2:  # Only consider jobs with multiple skills
                salary_value = extract_salary_value(job.get('salary'))
                job_type = normalize_job_type(job.get('title'))
                
                job_skills_data.append({
                    'skills': skills,
                    'salary': salary_value,
                    'job_type': job_type
                })
                
                for skill in skills:
                    skill_counts[skill] += 1
        
        # Filter skills that appear in at least 10 jobs
        common_skills = [skill for skill, count in skill_counts.items() if count >= 10]
        
        if len(common_skills) < 2:
            print("Not enough common skills found for correlation analysis")
            return False
        
        # Calculate skill combinations and their correlations
        skill_combinations = {}
        combination_salaries = defaultdict(list)
        combination_job_types = defaultdict(list)
        
        for job_data in job_skills_data:
            job_skills = [skill for skill in job_data['skills'] if skill in common_skills]
            
            if len(job_skills) >= 2:
                # Generate all pairs of skills in this job
                for skill_pair in combinations(sorted(job_skills), 2):
                    combo_key = f"{skill_pair[0]} + {skill_pair[1]}"
                    
                    if combo_key not in skill_combinations:
                        skill_combinations[combo_key] = 0
                    skill_combinations[combo_key] += 1
                    
                    if job_data['salary']:
                        combination_salaries[combo_key].append(job_data['salary'])
                    
                    combination_job_types[combo_key].append(job_data['job_type'])
        
        cursor.execute("DELETE FROM analysis_skills_correlation")
        results_stored = 0
        
        # Calculate correlation strength and store results
        total_jobs = len(job_skills_data)
        
        for combo, count in skill_combinations.items():
            if count >= 5:  # Only combinations that appear in at least 5 jobs
                correlation_strength = count / total_jobs
                avg_salary = mean(combination_salaries[combo]) if combination_salaries[combo] else 0
                common_job_types = [jt for jt, cnt in Counter(combination_job_types[combo]).most_common(3)]
                
                related_jobs = get_related_jobs(connection, combo)
                
                insert_query = \"\"\"
                INSERT INTO analysis_skills_correlation 
                (skill_combination, correlation_strength, job_count, avg_salary, job_types, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                \"\"\"
                
                cursor.execute(insert_query, (
                    combo, round(correlation_strength, 3), count,
                    round(avg_salary, 2), json.dumps(common_job_types), related_jobs
                ))
                results_stored += 1
        
        print(f"✅ Analysis completed! Stored {results_stored} skill correlation records")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
"""

# Save these files
with open('analysis/emerging_job_titles.py', 'w') as f:
    f.write(analysis_13_content)

with open('analysis/experience_requirements_trends.py', 'w') as f:
    f.write(analysis_14_content)

with open('analysis/skills_correlation_analysis.py', 'w') as f:
    f.write(analysis_15_content)

print("✓ Created analysis/emerging_job_titles.py")
print("✓ Created analysis/experience_requirements_trends.py")
print("✓ Created analysis/skills_correlation_analysis.py")

print("\\n🎉 All 15 analysis modules have been created successfully!")