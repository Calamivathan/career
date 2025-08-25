#!/usr/bin/env python3
"""
Analysis: Experience Level Distribution
Analyzes job distribution across different experience levels
"""

import pymysql
import json
import re
from collections import defaultdict, Counter
from statistics import mean

def categorize_experience(min_exp, max_exp, experience_text):
    """Categorize experience level"""
    try:
        min_val = float(min_exp) if min_exp else 0
        max_val = float(max_exp) if max_exp else min_val

        if min_val == 0 and max_val <= 1:
            return 'Entry Level (0-1 years)'
        elif min_val <= 2 and max_val <= 3:
            return 'Junior Level (1-3 years)'
        elif min_val <= 4 and max_val <= 7:
            return 'Mid Level (3-7 years)'
        elif min_val <= 8 and max_val <= 12:
            return 'Senior Level (7-12 years)'
        else:
            return 'Expert Level (12+ years)'
    except (ValueError, TypeError):
        if experience_text:
            exp_text = experience_text.lower()
            if 'fresher' in exp_text or '0' in exp_text:
                return 'Entry Level (0-1 years)'
            elif any(word in exp_text for word in ['1', '2', '3']):
                return 'Junior Level (1-3 years)'
            elif any(word in exp_text for word in ['4', '5', '6', '7']):
                return 'Mid Level (3-7 years)'
            else:
                return 'Senior Level (7-12 years)'
        return 'Unknown'

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

def get_related_jobs(connection, experience_level, limit=5):
    try:
        cursor = connection.cursor()
        if 'Entry' in experience_level:
            query = """
            SELECT title, company, location, salary, job_id
            FROM jobs_latest 
            WHERE (minimum_experience = 0 OR minimum_experience IS NULL OR experience LIKE '%fresher%')
            LIMIT %s
            """
            cursor.execute(query, (limit,))
        else:
            query = """
            SELECT title, company, location, salary, job_id
            FROM jobs_latest 
            LIMIT %s
            """
            cursor.execute(query, (limit,))

        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id']} for job in jobs]
        return json.dumps(related_jobs)
    except Exception as e:
        print(f"Error getting related jobs: {e}")
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        print("🔍 Fetching job data for experience level analysis...")

        query = """
        SELECT title, minimum_experience, maximum_experience, experience, salary, tags_and_skills
        FROM jobs_complete 
        """

        cursor.execute(query)
        jobs = cursor.fetchall()

        if not jobs:
            print("No jobs found")
            return False

        print(f"📊 Processing {len(jobs)} jobs...")

        experience_data = defaultdict(lambda: {'job_count': 0, 'salaries': [], 'all_skills': []})

        for job in jobs:
            exp_category = categorize_experience(
                job.get('minimum_experience'),
                job.get('maximum_experience'),
                job.get('experience')
            )

            experience_data[exp_category]['job_count'] += 1

            salary_value = extract_salary_value(job.get('salary'))
            if salary_value and salary_value > 0:
                experience_data[exp_category]['salaries'].append(salary_value)

            skills = extract_skills_from_text(job.get('tags_and_skills'))
            experience_data[exp_category]['all_skills'].extend(skills)

        cursor.execute("DELETE FROM analysis_experience_distribution")

        total_jobs = sum(data['job_count'] for data in experience_data.values())
        results_stored = 0

        for exp_level, data in experience_data.items():
            if exp_level != 'Unknown' and data['job_count'] > 0:
                percentage = (data['job_count'] / total_jobs) * 100
                avg_salary = mean(data['salaries']) if data['salaries'] else 0
                top_skills = [skill for skill, count in Counter(data['all_skills']).most_common(5)]
                related_jobs = get_related_jobs(connection, exp_level)

                insert_query = """
                INSERT INTO analysis_experience_distribution 
                (experience_level, job_count, percentage, avg_salary, top_skills, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                """

                cursor.execute(insert_query, (
                    exp_level,
                    data['job_count'],
                    round(percentage, 2),
                    round(avg_salary, 2),
                    json.dumps(top_skills),
                    related_jobs
                ))
                results_stored += 1

        print(f"✅ Analysis completed! Stored {results_stored} experience level records")
        return True

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
