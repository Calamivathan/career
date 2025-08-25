#!/usr/bin/env python3
"""
Analysis: Skills Correlation Analysis
Analyzes which skills commonly appear together in job requirements
"""

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
    numbers = re.findall(r'\d+(?:\.\d+)?', salary_str)
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
            query = """SELECT title, company, location, salary, job_id FROM jobs_latest 
                       WHERE tags_and_skills LIKE %s AND tags_and_skills LIKE %s LIMIT %s"""
            pattern1 = f"%{skills[0]}%"
            pattern2 = f"%{skills[1]}%"
            cursor.execute(query, (pattern1, pattern2, limit))
        else:
            query = """SELECT title, company, location, salary, job_id FROM jobs_latest LIMIT %s"""
            cursor.execute(query, (limit,))

        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id']} for job in jobs]
        return json.dumps(related_jobs)
    except:
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        query = """SELECT title, tags_and_skills, job_description, salary FROM jobs_complete 
                   WHERE tags_and_skills IS NOT NULL AND tags_and_skills != ''"""
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

                insert_query = """
                INSERT INTO analysis_skills_correlation 
                (skill_combination, correlation_strength, job_count, avg_salary, job_types, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                """

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
