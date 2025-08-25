#!/usr/bin/env python3
"""
Analysis: Most Competitive Jobs
Analyzes jobs with highest competition ratios (applications per opening)
"""

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
        query = """SELECT title, company, location, salary, job_id, apply_count, openings FROM jobs_latest 
                   WHERE title LIKE %s ORDER BY CAST(apply_count AS UNSIGNED) DESC LIMIT %s"""
        cursor.execute(query, (search_pattern, limit))
        jobs = cursor.fetchall()
        related_jobs = [{'title': job['title'], 'company': job['company'], 'location': job['location'], 'salary': job['salary'], 'job_id': job['job_id'], 'apply_count': job.get('apply_count', 0), 'openings': job.get('openings', 1)} for job in jobs]
        return json.dumps(related_jobs)
    except:
        return "[]"

def run_analysis(connection):
    try:
        cursor = connection.cursor()
        query = """SELECT title, apply_count, openings FROM jobs_complete 
                   WHERE apply_count IS NOT NULL AND apply_count > 0 AND openings IS NOT NULL AND openings > 0"""
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

            insert_query = """
            INSERT INTO analysis_competitive_jobs 
            (job_title, avg_applications_per_opening, total_applications, total_openings, competition_level, related_jobs)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

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
