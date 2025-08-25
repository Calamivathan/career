#!/usr/bin/env python3
"""
Analysis: Emerging Job Titles
Analyzes new and trending job titles that are gaining popularity
"""

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

def clean_job_title(title):
    """Clean and normalize job titles"""
    if not title:
        return None

    # Remove common prefixes and suffixes that don't add meaning
    title_clean = re.sub(r'^(senior|junior|sr|jr)\s+', '', title.strip(), flags=re.IGNORECASE)
    title_clean = re.sub(r'\s+(i{1,3}|1|2|3)$', '', title_clean, flags=re.IGNORECASE)

    return title_clean.strip().title() if len(title_clean) > 3 else None

def get_related_jobs(connection, job_title, limit=5):
    try:
        cursor = connection.cursor()
        query = """SELECT title, company, location, salary, job_id FROM jobs_latest 
                   WHERE title LIKE %s LIMIT %s"""
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
        recent_query = """SELECT title, tags_and_skills, salary, created_at FROM jobs_complete 
                         WHERE created_at >= %s AND title IS NOT NULL"""
        cursor.execute(recent_query, (six_months_ago.strftime('%Y-%m-%d'),))
        recent_jobs = cursor.fetchall()

        # Fetch older jobs for comparison
        older_query = """SELECT title, tags_and_skills, salary, created_at FROM jobs_complete 
                        WHERE created_at < %s AND title IS NOT NULL"""
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

            insert_query = """
            INSERT INTO analysis_emerging_job_titles 
            (job_title, recent_count, growth_rate, avg_salary, key_skills, related_jobs)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

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
