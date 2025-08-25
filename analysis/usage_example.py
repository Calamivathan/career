#!/usr/bin/env python3
"""
Usage Example: How to use the Job Data Analysis System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis_runner import AnalysisRunner, DB_CONFIG
import pymysql

def example_usage():
    """Example of how to use the analysis system"""

    print("Job Data Analysis System - Usage Example")
    print("="*50)

    # Initialize the analysis runner
    runner = AnalysisRunner()

    # Example 1: Run a single analysis
    print("\n1. Running single analysis (Top Skills by Job Type)...")
    if runner.connect_database():
        runner.create_analysis_tables()
        success = runner.run_single_analysis('top_skills_by_job_type')

        if success:
            # Query results
            cursor = runner.connection.cursor()
            cursor.execute("""
                SELECT job_type, skill, frequency, percentage 
                FROM analysis_top_skills_by_job_type 
                ORDER BY frequency DESC 
                LIMIT 10
            """)

            results = cursor.fetchall()
            print("\nTop 10 Skills Results:")
            for result in results:
                print(f"  {result['job_type']}: {result['skill']} ({result['frequency']} jobs, {result['percentage']}%)")

        runner.close_database()

    # Example 2: Query analysis results
    print("\n2. Querying existing analysis results...")
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Get top paying jobs
    cursor.execute("SELECT job_title, avg_salary FROM analysis_top_paying_jobs ORDER BY avg_salary DESC LIMIT 5")
    top_paying = cursor.fetchall()

    if top_paying:
        print("\nTop 5 Highest Paying Jobs:")
        for job in top_paying:
            salary_lpa = job['avg_salary'] / 100000
            print(f"  {job['job_title']}: {salary_lpa:.1f} LPA")

    connection.close()

if __name__ == "__main__":
    example_usage()
