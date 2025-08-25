# First, let's fix the database schema issues and skill extraction problems

# Fix the analysis_runner.py with larger column sizes
fixed_analysis_runner = """#!/usr/bin/env python3
\"\"\"
Job Data Analysis Runner
Main script to execute all job market analyses
\"\"\"

import sys
import os
import importlib.util
import pymysql
from datetime import datetime
import traceback

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'hrmoihtt_hrtoolusers', 
    'password': 'FsPyjP6hPc6yReV11111111',
    'database': 'hrmoihtt_hrtoolusers',
    'cursorclass': pymysql.cursors.DictCursor,
    'charset': 'utf8mb4',
    'autocommit': True,
    'port': 3306
}

class AnalysisRunner:
    def __init__(self):
        self.connection = None
        self.analyses = [
            'top_skills_by_job_type',
            'trending_skills_analysis', 
            'top_paying_jobs',
            'most_demanded_jobs',
            'best_locations_by_job_type',
            'experience_level_distribution',
            'company_hiring_trends',
            'salary_by_experience_trends',
            'govt_vs_private_analysis',
            'job_duration_analysis',
            'skills_demand_by_location',
            'most_competitive_jobs',
            'emerging_job_titles',
            'experience_requirements_trends',
            'skills_correlation_analysis'
        ]
    
    def connect_database(self):
        \"\"\"Establish database connection\"\"\"
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            print("✓ Database connection established")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def close_database(self):
        \"\"\"Close database connection\"\"\"
        if self.connection:
            self.connection.close()
            print("✓ Database connection closed")
    
    def create_analysis_tables(self):
        \"\"\"Create tables for storing analysis results\"\"\"
        table_schemas = {
            'analysis_top_skills_by_job_type': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_top_skills_by_job_type (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    job_type VARCHAR(500),
                    skill TEXT,
                    frequency INT,
                    percentage DECIMAL(5,2),
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
            
            'analysis_trending_skills': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_trending_skills (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    skill TEXT,
                    current_frequency INT,
                    growth_rate DECIMAL(10,2),
                    trend_period VARCHAR(100),
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
            
            'analysis_top_paying_jobs': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_top_paying_jobs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    job_title VARCHAR(500),
                    avg_salary DECIMAL(12,2),
                    min_salary DECIMAL(12,2),
                    max_salary DECIMAL(12,2),
                    job_count INT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_most_demanded_jobs': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_most_demanded_jobs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    job_title VARCHAR(500),
                    total_applications INT,
                    total_openings INT,
                    demand_ratio DECIMAL(10,2),
                    avg_competition DECIMAL(10,2),
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_best_locations': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_best_locations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    job_type VARCHAR(500),
                    location VARCHAR(500),
                    job_count INT,
                    avg_salary DECIMAL(12,2),
                    total_openings INT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_experience_distribution': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_experience_distribution (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    experience_level VARCHAR(200),
                    job_count INT,
                    percentage DECIMAL(5,2),
                    avg_salary DECIMAL(12,2),
                    top_skills TEXT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_company_hiring_trends': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_company_hiring_trends (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company VARCHAR(500),
                    total_jobs INT,
                    total_openings INT,
                    avg_salary DECIMAL(12,2),
                    top_job_types TEXT,
                    hiring_trend VARCHAR(100),
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_salary_experience_trends': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_salary_experience_trends (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    experience_range VARCHAR(100),
                    avg_salary DECIMAL(12,2),
                    median_salary DECIMAL(12,2),
                    salary_growth_rate DECIMAL(5,2),
                    job_count INT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_govt_vs_private': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_govt_vs_private (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sector VARCHAR(100),
                    job_count INT,
                    avg_salary DECIMAL(12,2),
                    top_job_types TEXT,
                    total_openings INT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_job_duration': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_job_duration (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    duration_category VARCHAR(200),
                    job_count INT,
                    percentage DECIMAL(5,2),
                    avg_salary DECIMAL(12,2),
                    popular_job_types TEXT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_skills_by_location': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_skills_by_location (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    location VARCHAR(500),
                    skill TEXT,
                    frequency INT,
                    job_count INT,
                    avg_salary DECIMAL(12,2),
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_competitive_jobs': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_competitive_jobs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    job_title VARCHAR(500),
                    avg_applications_per_opening DECIMAL(10,2),
                    total_applications INT,
                    total_openings INT,
                    competition_level VARCHAR(100),
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_emerging_job_titles': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_emerging_job_titles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    job_title VARCHAR(500),
                    recent_count INT,
                    growth_rate DECIMAL(10,2),
                    avg_salary DECIMAL(12,2),
                    key_skills TEXT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_experience_requirements': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_experience_requirements (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    job_category VARCHAR(500),
                    avg_min_experience DECIMAL(5,2),
                    avg_max_experience DECIMAL(5,2),
                    experience_trend VARCHAR(100),
                    job_count INT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\",
                
            'analysis_skills_correlation': 
                \"\"\"CREATE TABLE IF NOT EXISTS analysis_skills_correlation (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    skill_combination TEXT,
                    correlation_strength DECIMAL(5,3),
                    job_count INT,
                    avg_salary DECIMAL(12,2),
                    job_types TEXT,
                    related_jobs TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\"\"\"
        }
        
        cursor = self.connection.cursor()
        for table_name, schema in table_schemas.items():
            try:
                cursor.execute(schema)
                print(f"✓ Created/verified table: {table_name}")
            except Exception as e:
                print(f"✗ Error creating table {table_name}: {e}")
    
    def load_analysis_module(self, analysis_name):
        \"\"\"Dynamically load analysis module\"\"\"
        try:
            module_path = os.path.join('analysis', f'{analysis_name}.py')
            if not os.path.exists(module_path):
                print(f"✗ Analysis file not found: {module_path}")
                return None
            
            spec = importlib.util.spec_from_file_location(analysis_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            print(f"✗ Error loading analysis module {analysis_name}: {e}")
            traceback.print_exc()
            return None
    
    def run_single_analysis(self, analysis_name):
        \"\"\"Run a single analysis\"\"\"
        print(f"\\n{'='*50}")
        print(f"Running analysis: {analysis_name}")
        print(f"{'='*50}")
        
        try:
            # Load the analysis module
            module = self.load_analysis_module(analysis_name)
            if not module:
                return False
            
            # Check if the module has the required function
            if not hasattr(module, 'run_analysis'):
                print(f"✗ Analysis module {analysis_name} missing run_analysis function")
                return False
            
            # Run the analysis
            success = module.run_analysis(self.connection)
            
            if success:
                print(f"✓ Analysis {analysis_name} completed successfully")
                return True
            else:
                print(f"✗ Analysis {analysis_name} failed")
                return False
                
        except Exception as e:
            print(f"✗ Error running analysis {analysis_name}: {e}")
            traceback.print_exc()
            return False
    
    def run_all_analyses(self):
        \"\"\"Run all analyses\"\"\"
        print("\\n" + "="*60)
        print("STARTING JOB DATA ANALYSIS SUITE")
        print("="*60)
        
        if not self.connect_database():
            return False
        
        # Create analysis tables
        print("\\nCreating analysis tables...")
        self.create_analysis_tables()
        
        # Run each analysis
        successful_analyses = 0
        failed_analyses = []
        
        for analysis in self.analyses:
            success = self.run_single_analysis(analysis)
            if success:
                successful_analyses += 1
            else:
                failed_analyses.append(analysis)
        
        # Print summary
        print("\\n" + "="*60)
        print("ANALYSIS SUITE SUMMARY")
        print("="*60)
        print(f"Total analyses: {len(self.analyses)}")
        print(f"Successful: {successful_analyses}")
        print(f"Failed: {len(failed_analyses)}")
        
        if failed_analyses:
            print("\\nFailed analyses:")
            for analysis in failed_analyses:
                print(f"  - {analysis}")
        
        self.close_database()
        return len(failed_analyses) == 0

def main():
    \"\"\"Main function\"\"\"
    if len(sys.argv) > 1 and sys.argv[1] == 'single':
        if len(sys.argv) > 2:
            # Run single analysis
            analysis_name = sys.argv[2]
            runner = AnalysisRunner()
            if runner.connect_database():
                runner.create_analysis_tables()
                runner.run_single_analysis(analysis_name)
                runner.close_database()
        else:
            print("Please specify analysis name for single run")
            print("Available analyses:")
            runner = AnalysisRunner()
            for analysis in runner.analyses:
                print(f"  - {analysis}")
    else:
        # Run all analyses
        runner = AnalysisRunner()
        runner.run_all_analyses()

if __name__ == "__main__":
    main()
"""

# Save the fixed analysis runner
with open('analysis_runner.py', 'w') as f:
    f.write(fixed_analysis_runner)

print("✓ Fixed analysis_runner.py with larger column sizes")