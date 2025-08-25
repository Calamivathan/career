#!/usr/bin/env python3
"""
Job Analysis Dashboard
Creates visualizations and reports from analysis results
"""

import pymysql
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime
import os

# Database configuration (same as analysis_runner.py)
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

class JobAnalysisDashboard:
    def __init__(self):
        self.connection = None
        self.output_dir = 'dashboard_outputs'

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    def connect_database(self):
        """Establish database connection"""
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            print("✓ Database connection established")
            return True
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False

    def close_database(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("✓ Database connection closed")

    def generate_skills_report(self):
        """Generate top skills analysis report"""
        try:
            print("📊 Generating Skills Analysis Report...")

            # Get top skills by job type
            query = """
            SELECT job_type, skill, frequency, percentage 
            FROM analysis_top_skills_by_job_type 
            ORDER BY frequency DESC 
            LIMIT 50
            """

            df = pd.read_sql(query, self.connection)

            if df.empty:
                print("No skills data found")
                return

            # Create visualization
            plt.figure(figsize=(15, 10))

            # Top 20 skills overall
            top_skills = df.groupby('skill')['frequency'].sum().sort_values(ascending=False).head(20)

            plt.subplot(2, 2, 1)
            top_skills.plot(kind='bar')
            plt.title('Top 20 Most Demanded Skills Overall')
            plt.xlabel('Skills')
            plt.ylabel('Frequency')
            plt.xticks(rotation=45)

            # Skills by job type (top 5 job types)
            top_job_types = df.groupby('job_type')['frequency'].sum().sort_values(ascending=False).head(5)

            plt.subplot(2, 2, 2)
            job_type_skills = df[df['job_type'].isin(top_job_types.index)]
            job_type_pivot = job_type_skills.groupby(['job_type', 'skill'])['frequency'].sum().unstack(fill_value=0)

            # Get top 10 skills for heatmap
            top_10_skills = job_type_skills.groupby('skill')['frequency'].sum().sort_values(ascending=False).head(10)
            job_type_pivot_subset = job_type_pivot[top_10_skills.index]

            sns.heatmap(job_type_pivot_subset, annot=True, fmt='d', cmap='YlOrRd')
            plt.title('Skills Demand by Job Type (Top 5 Job Types)')
            plt.xlabel('Skills')
            plt.ylabel('Job Types')

            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/skills_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()

            # Create skills summary CSV
            skills_summary = df.groupby('skill').agg({
                'frequency': 'sum',
                'job_type': 'count'
            }).rename(columns={'job_type': 'job_types_count'}).sort_values('frequency', ascending=False)

            skills_summary.to_csv(f'{self.output_dir}/skills_summary.csv')
            print(f"✓ Skills analysis saved to {self.output_dir}/")

        except Exception as e:
            print(f"❌ Skills report generation failed: {e}")

    def generate_salary_report(self):
        """Generate salary analysis report"""
        try:
            print("💰 Generating Salary Analysis Report...")

            # Get salary data
            query = """
            SELECT job_title, avg_salary, min_salary, max_salary, job_count 
            FROM analysis_top_paying_jobs 
            WHERE avg_salary > 0
            ORDER BY avg_salary DESC 
            LIMIT 30
            """

            df = pd.read_sql(query, self.connection)

            if df.empty:
                print("No salary data found")
                return

            # Convert to LPA for better readability
            df['avg_salary_lpa'] = df['avg_salary'] / 100000
            df['min_salary_lpa'] = df['min_salary'] / 100000
            df['max_salary_lpa'] = df['max_salary'] / 100000

            plt.figure(figsize=(15, 10))

            # Top 15 paying jobs
            plt.subplot(2, 2, 1)
            top_15 = df.head(15)
            plt.barh(range(len(top_15)), top_15['avg_salary_lpa'])
            plt.yticks(range(len(top_15)), top_15['job_title'])
            plt.xlabel('Average Salary (LPA)')
            plt.title('Top 15 Highest Paying Jobs')
            plt.gca().invert_yaxis()

            # Salary distribution
            plt.subplot(2, 2, 2)
            plt.hist(df['avg_salary_lpa'], bins=20, alpha=0.7, color='skyblue')
            plt.xlabel('Average Salary (LPA)')
            plt.ylabel('Number of Job Titles')
            plt.title('Salary Distribution')

            # Salary vs Job Count
            plt.subplot(2, 2, 3)
            plt.scatter(df['job_count'], df['avg_salary_lpa'], alpha=0.6)
            plt.xlabel('Number of Job Postings')
            plt.ylabel('Average Salary (LPA)')
            plt.title('Salary vs Job Availability')

            # Salary range analysis
            plt.subplot(2, 2, 4)
            salary_ranges = df[df['max_salary_lpa'] > df['min_salary_lpa']].head(10)
            x_pos = range(len(salary_ranges))
            plt.barh(x_pos, salary_ranges['max_salary_lpa'] - salary_ranges['min_salary_lpa'], 
                    left=salary_ranges['min_salary_lpa'], alpha=0.7)
            plt.yticks(x_pos, salary_ranges['job_title'])
            plt.xlabel('Salary Range (LPA)')
            plt.title('Top 10 Salary Ranges')
            plt.gca().invert_yaxis()

            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/salary_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()

            # Save salary summary
            df[['job_title', 'avg_salary_lpa', 'min_salary_lpa', 'max_salary_lpa', 'job_count']].to_csv(
                f'{self.output_dir}/salary_summary.csv', index=False)
            print(f"✓ Salary analysis saved to {self.output_dir}/")

        except Exception as e:
            print(f"❌ Salary report generation failed: {e}")

    def generate_location_report(self):
        """Generate location analysis report"""
        try:
            print("🌍 Generating Location Analysis Report...")

            query = """
            SELECT job_type, location, job_count, avg_salary, total_openings 
            FROM analysis_best_locations 
            ORDER BY job_count DESC 
            LIMIT 100
            """

            df = pd.read_sql(query, self.connection)

            if df.empty:
                print("No location data found")
                return

            df['avg_salary_lpa'] = df['avg_salary'] / 100000

            plt.figure(figsize=(15, 10))

            # Top cities by job count
            plt.subplot(2, 2, 1)
            top_cities = df.groupby('location')['job_count'].sum().sort_values(ascending=False).head(15)
            plt.bar(range(len(top_cities)), top_cities.values)
            plt.xticks(range(len(top_cities)), top_cities.index, rotation=45)
            plt.ylabel('Total Jobs')
            plt.title('Top 15 Cities by Job Count')

            # Average salary by city
            plt.subplot(2, 2, 2)
            city_salary = df.groupby('location')['avg_salary_lpa'].mean().sort_values(ascending=False).head(15)
            plt.bar(range(len(city_salary)), city_salary.values, color='orange')
            plt.xticks(range(len(city_salary)), city_salary.index, rotation=45)
            plt.ylabel('Average Salary (LPA)')
            plt.title('Top 15 Cities by Average Salary')

            # Job opportunities heatmap
            plt.subplot(2, 2, 3)
            location_job_type = df.groupby(['location', 'job_type'])['job_count'].sum().unstack(fill_value=0)

            # Get top 10 locations and top 5 job types
            top_10_locations = df.groupby('location')['job_count'].sum().sort_values(ascending=False).head(10)
            top_5_job_types = df.groupby('job_type')['job_count'].sum().sort_values(ascending=False).head(5)

            subset = location_job_type.loc[top_10_locations.index, top_5_job_types.index]
            sns.heatmap(subset, annot=True, fmt='d', cmap='Blues')
            plt.title('Job Opportunities by Location and Type')
            plt.xlabel('Job Types')
            plt.ylabel('Locations')

            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/location_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()

            # Save location summary
            location_summary = df.groupby('location').agg({
                'job_count': 'sum',
                'avg_salary_lpa': 'mean',
                'total_openings': 'sum',
                'job_type': 'count'
            }).rename(columns={'job_type': 'job_types_available'}).sort_values('job_count', ascending=False)

            location_summary.to_csv(f'{self.output_dir}/location_summary.csv')
            print(f"✓ Location analysis saved to {self.output_dir}/")

        except Exception as e:
            print(f"❌ Location report generation failed: {e}")

    def generate_trends_report(self):
        """Generate trending analysis report"""
        try:
            print("📈 Generating Trends Analysis Report...")

            # Get trending skills
            query1 = """
            SELECT skill, current_frequency, growth_rate, trend_period 
            FROM analysis_trending_skills 
            ORDER BY growth_rate DESC 
            LIMIT 30
            """

            trending_df = pd.read_sql(query1, self.connection)

            # Get competitive jobs
            query2 = """
            SELECT job_title, avg_applications_per_opening, total_applications, competition_level 
            FROM analysis_competitive_jobs 
            ORDER BY avg_applications_per_opening DESC 
            LIMIT 20
            """

            competitive_df = pd.read_sql(query2, self.connection)

            plt.figure(figsize=(15, 10))

            if not trending_df.empty:
                # Trending skills
                plt.subplot(2, 2, 1)
                top_trending = trending_df.head(15)
                plt.barh(range(len(top_trending)), top_trending['growth_rate'])
                plt.yticks(range(len(top_trending)), top_trending['skill'])
                plt.xlabel('Growth Rate (%)')
                plt.title('Top 15 Trending Skills')
                plt.gca().invert_yaxis()

            if not competitive_df.empty:
                # Most competitive jobs
                plt.subplot(2, 2, 2)
                top_competitive = competitive_df.head(10)
                plt.bar(range(len(top_competitive)), top_competitive['avg_applications_per_opening'])
                plt.xticks(range(len(top_competitive)), top_competitive['job_title'], rotation=45)
                plt.ylabel('Applications per Opening')
                plt.title('Top 10 Most Competitive Jobs')

            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/trends_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()

            # Save trends data
            if not trending_df.empty:
                trending_df.to_csv(f'{self.output_dir}/trending_skills.csv', index=False)
            if not competitive_df.empty:
                competitive_df.to_csv(f'{self.output_dir}/competitive_jobs.csv', index=False)

            print(f"✓ Trends analysis saved to {self.output_dir}/")

        except Exception as e:
            print(f"❌ Trends report generation failed: {e}")

    def generate_comprehensive_report(self):
        """Generate a comprehensive summary report"""
        try:
            print("📋 Generating Comprehensive Summary Report...")

            report_content = f"""# Job Market Analysis Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary
This report provides insights into the current job market based on comprehensive data analysis.

"""

            # Get summary statistics from various analyses
            analyses = [
                ('Skills Analysis', 'analysis_top_skills_by_job_type', ['job_type', 'skill', 'frequency']),
                ('Top Paying Jobs', 'analysis_top_paying_jobs', ['job_title', 'avg_salary']),
                ('Location Analysis', 'analysis_best_locations', ['location', 'job_count']),
                ('Experience Distribution', 'analysis_experience_distribution', ['experience_level', 'percentage']),
                ('Trending Skills', 'analysis_trending_skills', ['skill', 'growth_rate'])
            ]

            for analysis_name, table_name, columns in analyses:
                try:
                    query = f"SELECT * FROM {table_name} LIMIT 10"
                    df = pd.read_sql(query, self.connection)

                    if not df.empty:
                        report_content += f"\n## {analysis_name}\n"
                        report_content += f"Total records: {len(df)}\n"

                        # Add top 5 entries
                        report_content += f"\nTop 5 entries:\n"
                        for i, row in df.head(5).iterrows():
                            if analysis_name == 'Top Paying Jobs' and 'avg_salary' in row:
                                salary_lpa = row['avg_salary'] / 100000 if row['avg_salary'] else 0
                                report_content += f"- {row[columns[0]]}: {salary_lpa:.1f} LPA\n"
                            else:
                                values = [str(row[col]) for col in columns if col in row]
                                report_content += f"- {': '.join(values)}\n"

                        report_content += "\n"

                except Exception as e:
                    report_content += f"\n## {analysis_name}\nData not available: {e}\n\n"

            # Save the report
            with open(f'{self.output_dir}/comprehensive_report.md', 'w') as f:
                f.write(report_content)

            print(f"✓ Comprehensive report saved to {self.output_dir}/comprehensive_report.md")

        except Exception as e:
            print(f"❌ Comprehensive report generation failed: {e}")

    def run_all_reports(self):
        """Generate all analysis reports"""
        print("🚀 Starting Dashboard Generation...")
        print("="*50)

        if not self.connect_database():
            return False

        try:
            # Generate all reports
            self.generate_skills_report()
            self.generate_salary_report()
            self.generate_location_report()
            self.generate_trends_report()
            self.generate_comprehensive_report()

            print("\n" + "="*50)
            print("✅ All reports generated successfully!")
            print(f"📁 Check the '{self.output_dir}' directory for all outputs:")
            print("  • skills_analysis.png")
            print("  • salary_analysis.png")
            print("  • location_analysis.png")
            print("  • trends_analysis.png")
            print("  • skills_summary.csv")
            print("  • salary_summary.csv")
            print("  • location_summary.csv")
            print("  • trending_skills.csv")
            print("  • competitive_jobs.csv")
            print("  • comprehensive_report.md")

            return True

        except Exception as e:
            print(f"❌ Dashboard generation failed: {e}")
            return False
        finally:
            self.close_database()

def main():
    """Main function"""
    dashboard = JobAnalysisDashboard()
    dashboard.run_all_reports()

if __name__ == "__main__":
    main()
