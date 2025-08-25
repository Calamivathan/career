#!/usr/bin/env python3
"""
Analysis: Experience Requirements Trends
Analyzes how experience requirements are changing across job categories
"""

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

        # Get current date and calculate periods
        now = datetime.now()
        six_months_ago = now - timedelta(days=180)

        # Fetch recent jobs
        recent_query = """SELECT title, minimum_experience, maximum_experience FROM jobs_complete 
                         WHERE created_at >= %s AND title IS NOT NULL"""
        cursor.execute(recent_query, (six_months_ago.strftime('%Y-%m-%d'),))
        recent_jobs = cursor.fetchall()

        # Fetch older jobs
        older_query = """SELECT title, minimum_experience, maximum_experience FROM jobs_complete 
                        WHERE created_at < %s AND title IS NOT NULL"""
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

                insert_query = """
                INSERT INTO analysis_experience_requirements 
                (job_category, avg_min_experience, avg_max_experience, experience_trend, job_count, related_jobs)
                VALUES (%s, %s, %s, %s, %s, %s)
                """

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
