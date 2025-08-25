#!/usr/bin/env python3
"""
Setup Script for Job Data Analysis System
Automates the initial setup and verification
"""

import os
import sys
import subprocess
import pymysql
from analysis_runner import DB_CONFIG

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True)
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🔗 Testing database connection...")
    try:
        connection = pymysql.connect(**DB_CONFIG)

        # Test if source tables exist
        cursor = connection.cursor()

        # Check jobs_complete table
        cursor.execute("SHOW TABLES LIKE 'jobs_complete'")
        if not cursor.fetchone():
            print("⚠️  Warning: 'jobs_complete' table not found")
            print("   This table is required for historical analysis")
        else:
            cursor.execute("SELECT COUNT(*) as count FROM jobs_complete")
            count = cursor.fetchone()['count']
            print(f"✓ jobs_complete table found ({count:,} records)")

        # Check jobs_latest table
        cursor.execute("SHOW TABLES LIKE 'jobs_latest'")
        if not cursor.fetchone():
            print("⚠️  Warning: 'jobs_latest' table not found")
            print("   This table is required for related job recommendations")
        else:
            cursor.execute("SELECT COUNT(*) as count FROM jobs_latest")
            count = cursor.fetchone()['count']
            print(f"✓ jobs_latest table found ({count:,} records)")

        connection.close()
        print("✓ Database connection successful")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Please check:")
        print("   • Database server is running")
        print("   • Database credentials are correct")
        print("   • Database and tables exist")
        print("   • Network connectivity")
        return False

def create_directory_structure():
    """Create necessary directories"""
    directories = ['analysis', 'dashboard_outputs']

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Created directory: {directory}")
        else:
            print(f"✓ Directory exists: {directory}")

def verify_analysis_modules():
    """Verify all analysis modules are present"""
    expected_modules = [
        'top_skills_by_job_type.py',
        'trending_skills_analysis.py', 
        'top_paying_jobs.py',
        'most_demanded_jobs.py',
        'best_locations_by_job_type.py',
        'experience_level_distribution.py',
        'company_hiring_trends.py',
        'salary_by_experience_trends.py',
        'govt_vs_private_analysis.py',
        'job_duration_analysis.py',
        'skills_demand_by_location.py',
        'most_competitive_jobs.py',
        'emerging_job_titles.py',
        'experience_requirements_trends.py',
        'skills_correlation_analysis.py'
    ]

    missing_modules = []

    for module in expected_modules:
        module_path = os.path.join('analysis', module)
        if os.path.exists(module_path):
            print(f"✓ {module}")
        else:
            missing_modules.append(module)
            print(f"❌ {module} - Missing")

    if missing_modules:
        print(f"\n⚠️  {len(missing_modules)} analysis modules are missing")
        return False
    else:
        print(f"\n✓ All {len(expected_modules)} analysis modules found")
        return True

def run_test_analysis():
    """Run a test analysis to verify everything works"""
    print("\n🧪 Running test analysis...")
    try:
        from analysis_runner import AnalysisRunner

        runner = AnalysisRunner()
        if runner.connect_database():
            runner.create_analysis_tables()

            # Test with a simple analysis
            success = runner.run_single_analysis('experience_level_distribution')
            runner.close_database()

            if success:
                print("✅ Test analysis completed successfully")
                return True
            else:
                print("❌ Test analysis failed")
                return False
        else:
            print("❌ Could not connect to database for test")
            return False

    except Exception as e:
        print(f"❌ Test analysis failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Job Data Analysis System - Setup")
    print("="*50)

    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("Directory Structure", create_directory_structure),
        ("Dependencies", install_dependencies),
        ("Database Connection", test_database_connection),
        ("Analysis Modules", verify_analysis_modules),
    ]

    all_passed = True

    for check_name, check_function in checks:
        print(f"\n🔍 {check_name}:")
        if not check_function():
            all_passed = False

    if all_passed:
        print("\n" + "="*50)
        print("✅ SETUP COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\n🎯 Next Steps:")
        print("1. Run full analysis: python analysis_runner.py")
        print("2. Generate dashboard: python dashboard_generator.py")
        print("3. View results in database tables")
        print("\n📚 Documentation: README.md")
        print("💡 Examples: usage_example.py")

        # Optional: Run test analysis
        response = input("\n🧪 Run test analysis now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            run_test_analysis()
    else:
        print("\n" + "="*50)
        print("❌ SETUP INCOMPLETE")
        print("="*50)
        print("\n🔧 Please fix the issues above and run setup again")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
