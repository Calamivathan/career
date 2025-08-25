#!/usr/bin/env python3
"""
Comprehensive Data Export Utility
Exports all analysis results to various formats (JSON, CSV, Excel)
"""

import pymysql
import json
import pandas as pd
from datetime import datetime
import os

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

class JobAnalysisExporter:
    def __init__(self):
        self.connection = None
        self.export_dir = 'exports'
        self.analyses_data = {}

        # Create export directory
        os.makedirs(self.export_dir, exist_ok=True)

        # Define all analysis tables
        self.analysis_tables = {
            'top_skills_by_job_type': 'Top Skills by Job Type',
            'trending_skills': 'Trending Skills Analysis',
            'top_paying_jobs': 'Top Paying Jobs',
            'most_demanded_jobs': 'Most Demanded Jobs',
            'best_locations': 'Best Locations by Job Type',
            'experience_distribution': 'Experience Level Distribution',
            'company_hiring_trends': 'Company Hiring Trends',
            'salary_experience_trends': 'Salary by Experience Trends',
            'govt_vs_private': 'Government vs Private Analysis',
            'job_duration': 'Job Duration Analysis',
            'skills_by_location': 'Skills Demand by Location',
            'competitive_jobs': 'Most Competitive Jobs',
            'emerging_job_titles': 'Emerging Job Titles',
            'experience_requirements': 'Experience Requirements Trends',
            'skills_correlation': 'Skills Correlation Analysis'
        }

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

    def extract_analysis_data(self):
        """Extract data from all analysis tables"""
        cursor = self.connection.cursor()

        for table_key, display_name in self.analysis_tables.items():
            try:
                table_name = f'analysis_{table_key}'

                # Check if table exists
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if not cursor.fetchone():
                    print(f"⚠️  Table {table_name} not found, skipping...")
                    continue

                # Get all data
                query = f"""
                SELECT * FROM {table_name} 
                ORDER BY 
                    CASE 
                        WHEN '{table_key}' IN ('top_paying_jobs', 'trending_skills') THEN 
                            CAST(COALESCE(avg_salary, growth_rate, 0) AS DECIMAL(15,2))
                        WHEN '{table_key}' IN ('most_demanded_jobs', 'competitive_jobs') THEN 
                            CAST(COALESCE(total_applications, avg_applications_per_opening, 0) AS DECIMAL(15,2))
                        ELSE frequency 
                    END DESC
                LIMIT 500
                """

                cursor.execute(query)
                results = cursor.fetchall()

                if results:
                    # Clean and process the data
                    processed_results = []
                    for row in results:
                        # Convert to regular dict and handle JSON fields
                        processed_row = dict(row)

                        # Parse related_jobs JSON if present
                        if 'related_jobs' in processed_row and processed_row['related_jobs']:
                            try:
                                related_jobs = json.loads(processed_row['related_jobs'])
                                processed_row['related_jobs_count'] = len(related_jobs) if related_jobs else 0
                                processed_row['related_jobs_summary'] = '; '.join([
                                    f"{job.get('title', 'N/A')} at {job.get('company', 'N/A')}" 
                                    for job in related_jobs[:3]
                                ]) if related_jobs else 'None'
                            except:
                                processed_row['related_jobs_count'] = 0
                                processed_row['related_jobs_summary'] = 'None'

                        # Parse other JSON fields
                        for field in ['top_skills', 'key_skills', 'top_job_types', 'job_types']:
                            if field in processed_row and processed_row[field]:
                                try:
                                    json_data = json.loads(processed_row[field])
                                    processed_row[f'{field}_summary'] = ', '.join(json_data) if isinstance(json_data, list) else str(json_data)
                                except:
                                    processed_row[f'{field}_summary'] = str(processed_row[field])

                        # Format salary fields
                        for field in processed_row:
                            if 'salary' in field.lower() and isinstance(processed_row[field], (int, float)) and processed_row[field] > 0:
                                processed_row[f'{field}_lpa'] = round(processed_row[field] / 100000, 2)

                        # Format percentage fields
                        for field in processed_row:
                            if 'percentage' in field.lower() or 'rate' in field.lower():
                                if isinstance(processed_row[field], (int, float)):
                                    processed_row[field] = round(processed_row[field], 2)

                        processed_results.append(processed_row)

                    self.analyses_data[table_key] = {
                        'title': display_name,
                        'table_name': table_name,
                        'data': processed_results,
                        'count': len(processed_results)
                    }

                    print(f"✓ Extracted {len(processed_results)} records from {display_name}")
                else:
                    print(f"⚠️  No data found in {display_name}")

            except Exception as e:
                print(f"❌ Error extracting from {display_name}: {e}")

    def export_to_json(self):
        """Export all data to comprehensive JSON file"""
        try:
            export_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_analyses': len(self.analyses_data),
                    'total_records': sum(analysis['count'] for analysis in self.analyses_data.values()),
                    'export_version': '1.0'
                },
                'analyses': self.analyses_data
            }

            # Main comprehensive JSON
            json_file = os.path.join(self.export_dir, 'job_analysis_complete_data.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)

            # Individual JSON files for each analysis
            for analysis_key, analysis_data in self.analyses_data.items():
                individual_file = os.path.join(self.export_dir, f'{analysis_key}_data.json')
                with open(individual_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'title': analysis_data['title'],
                        'generated_at': datetime.now().isoformat(),
                        'count': analysis_data['count'],
                        'data': analysis_data['data']
                    }, f, indent=2, default=str, ensure_ascii=False)

            print(f"✓ Exported JSON files to {self.export_dir}/")
            return True

        except Exception as e:
            print(f"❌ JSON export failed: {e}")
            return False

    def export_to_csv(self):
        """Export each analysis to separate CSV files"""
        try:
            for analysis_key, analysis_data in self.analyses_data.items():
                if analysis_data['data']:
                    df = pd.DataFrame(analysis_data['data'])

                    # Remove complex JSON columns for CSV
                    columns_to_remove = [col for col in df.columns if col in ['related_jobs']]
                    df = df.drop(columns=columns_to_remove, errors='ignore')

                    # Clean column names
                    df.columns = [col.replace('_', ' ').title() for col in df.columns]

                    csv_file = os.path.join(self.export_dir, f'{analysis_key}.csv')
                    df.to_csv(csv_file, index=False, encoding='utf-8')

                    print(f"✓ Exported {analysis_data['title']} to CSV ({len(df)} rows)")

            return True

        except Exception as e:
            print(f"❌ CSV export failed: {e}")
            return False

    def export_to_excel(self):
        """Export all analyses to a single Excel file with multiple sheets"""
        try:
            excel_file = os.path.join(self.export_dir, 'job_analysis_complete_data.xlsx')

            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # Create summary sheet
                summary_data = []
                for analysis_key, analysis_data in self.analyses_data.items():
                    summary_data.append({
                        'Analysis': analysis_data['title'],
                        'Records Count': analysis_data['count'],
                        'Sheet Name': analysis_key[:31]  # Excel sheet name limit
                    })

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_sheet(writer, sheet_name='Summary', index=False)

                # Create individual sheets for each analysis
                for analysis_key, analysis_data in self.analyses_data.items():
                    if analysis_data['data']:
                        df = pd.DataFrame(analysis_data['data'])

                        # Remove complex JSON columns
                        columns_to_remove = [col for col in df.columns if col in ['related_jobs']]
                        df = df.drop(columns=columns_to_remove, errors='ignore')

                        # Clean column names
                        df.columns = [col.replace('_', ' ').title() for col in df.columns]

                        # Use first 31 characters for sheet name (Excel limit)
                        sheet_name = analysis_key[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

            print(f"✓ Exported Excel file: {excel_file}")
            return True

        except Exception as e:
            print(f"❌ Excel export failed: {e}")
            return False

    def create_summary_report(self):
        """Create a comprehensive summary report"""
        try:
            report_content = f"""# Job Market Analysis - Comprehensive Report
Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## Executive Summary
This report consolidates insights from {len(self.analyses_data)} different job market analyses, 
covering {sum(analysis['count'] for analysis in self.analyses_data.values())} total data points.

## Analysis Overview
"""

            for analysis_key, analysis_data in self.analyses_data.items():
                report_content += f"\n### {analysis_data['title']}\n"
                report_content += f"- **Records**: {analysis_data['count']}\n"

                if analysis_data['data']:
                    # Add top 3 insights for each analysis
                    report_content += f"- **Top Insights**:\n"

                    for i, record in enumerate(analysis_data['data'][:3], 1):
                        # Create insight based on analysis type
                        if 'job_type' in record and 'skill' in record:
                            report_content += f"  {i}. {record.get('skill', 'N/A')} is top skill for {record.get('job_type', 'N/A')} ({record.get('frequency', 0)} mentions)\n"
                        elif 'job_title' in record and 'avg_salary' in record:
                            salary_lpa = record.get('avg_salary', 0) / 100000 if record.get('avg_salary', 0) > 0 else 0
                            report_content += f"  {i}. {record.get('job_title', 'N/A')}: {salary_lpa:.1f} LPA average salary\n"
                        elif 'location' in record and 'job_count' in record:
                            report_content += f"  {i}. {record.get('location', 'N/A')}: {record.get('job_count', 0)} job opportunities\n"
                        else:
                            # Generic insight
                            first_meaningful_field = None
                            for field, value in record.items():
                                if field not in ['id', 'analysis_date', 'related_jobs'] and value:
                                    first_meaningful_field = f"{field.replace('_', ' ').title()}: {value}"
                                    break
                            if first_meaningful_field:
                                report_content += f"  {i}. {first_meaningful_field}\n"

                report_content += "\n"

            report_content += f"""
## Key Recommendations for Students

### 1. Skill Development Priority
Based on the trending skills analysis, focus on learning:
- High-growth skills with increasing demand
- Skills that correlate well with higher salaries
- Location-specific skills based on your target city

### 2. Career Path Planning
- Consider high-paying job categories for long-term growth
- Understand experience requirements for your target roles
- Evaluate government vs private sector opportunities

### 3. Geographic Considerations
- Identify best locations for your job type
- Consider salary differences across cities
- Factor in competition levels by location

### 4. Market Timing
- Monitor emerging job titles for new opportunities
- Track company hiring trends for application timing
- Understand seasonal patterns in job duration

## Data Files Generated
- `job_analysis_complete_data.json` - Comprehensive data export
- `job_analysis_complete_data.xlsx` - Excel workbook with all analyses
- Individual CSV files for each analysis
- Individual JSON files for programmatic access

## Next Steps
1. Review the detailed analysis in the Excel file
2. Use the web dashboard for interactive exploration
3. Monitor trends by running analyses regularly
4. Customize the insights based on your career goals

---
*This report is generated automatically from real job market data. 
For the most current insights, re-run the analyses regularly.*
"""

            report_file = os.path.join(self.export_dir, 'comprehensive_analysis_report.md')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"✓ Created comprehensive report: {report_file}")
            return True

        except Exception as e:
            print(f"❌ Report creation failed: {e}")
            return False

    def run_complete_export(self):
        """Run complete data export process"""
        print("🚀 Starting Comprehensive Data Export...")
        print("="*50)

        if not self.connect_database():
            return False

        try:
            # Extract all data
            print("\n📊 Extracting analysis data from database...")
            self.extract_analysis_data()

            if not self.analyses_data:
                print("❌ No analysis data found. Please run the analyses first.")
                return False

            # Export to different formats
            print("\n💾 Exporting to JSON format...")
            self.export_to_json()

            print("\n📈 Exporting to CSV format...")
            self.export_to_csv()

            print("\n📊 Exporting to Excel format...")
            self.export_to_excel()

            print("\n📋 Creating summary report...")
            self.create_summary_report()

            print("\n" + "="*50)
            print("✅ Complete Data Export Finished!")
            print("="*50)
            print(f"\n📁 All files exported to: {self.export_dir}/")
            print("\n📊 Files created:")
            print("  • job_analysis_complete_data.json - Full dataset")
            print("  • job_analysis_complete_data.xlsx - Excel workbook")
            print("  • comprehensive_analysis_report.md - Summary report")
            print("  • Individual CSV files for each analysis")
            print("  • Individual JSON files for each analysis")

            total_records = sum(analysis['count'] for analysis in self.analyses_data.values())
            print(f"\n📈 Export Summary:")
            print(f"  • Total analyses: {len(self.analyses_data)}")
            print(f"  • Total records: {total_records:,}")
            print(f"  • Export formats: JSON, CSV, Excel, Markdown")

            return True

        except Exception as e:
            print(f"❌ Export process failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.close_database()

def main():
    """Main function"""
    exporter = JobAnalysisExporter()
    exporter.run_complete_export()

if __name__ == "__main__":
    main()
