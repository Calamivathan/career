# Now let's create a comprehensive web-based dashboard that extracts all data and displays it beautifully

web_dashboard_content = """#!/usr/bin/env python3
\"\"\"
Web-based Job Analysis Dashboard
Creates a beautiful, interactive web dashboard displaying all analysis results
\"\"\"

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

class JobAnalysisDashboard:
    def __init__(self):
        self.connection = None
        self.dashboard_data = {}
        
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
    
    def extract_all_analysis_data(self):
        \"\"\"Extract data from all analysis tables\"\"\"
        analyses = {
            'top_skills_by_job_type': 'Top Skills by Job Type',
            'trending_skills': 'Trending Skills',
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
        
        for table_key, display_name in analyses.items():
            try:
                table_name = f'analysis_{table_key}'
                query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 100"
                
                cursor = self.connection.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                
                if results:
                    self.dashboard_data[table_key] = {
                        'title': display_name,
                        'data': results,
                        'count': len(results)
                    }
                    print(f"✓ Extracted {len(results)} records from {display_name}")
                else:
                    print(f"⚠️  No data found in {display_name}")
                    
            except Exception as e:
                print(f"❌ Error extracting from {display_name}: {e}")
    
    def export_data_to_json(self):
        \"\"\"Export all analysis data to JSON file\"\"\"
        try:
            output_data = {
                'generated_at': datetime.now().isoformat(),
                'total_analyses': len(self.dashboard_data),
                'analyses': self.dashboard_data
            }
            
            with open('dashboard_data.json', 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            print("✓ Exported all analysis data to dashboard_data.json")
            return True
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            return False
    
    def generate_html_dashboard(self):
        \"\"\"Generate a beautiful HTML dashboard\"\"\"
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Market Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }}
        
        .dashboard-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            margin: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            color: #2c3e50;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stats-card {{
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border-radius: 15px;
            padding: 25px;
            margin: 10px;
            text-align: center;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .stats-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stats-card h3 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        
        .analysis-section {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .analysis-title {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .data-table {{
            margin-top: 20px;
        }}
        
        .table {{
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .table thead {{
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
        }}
        
        .table tbody tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .badge-custom {{
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
        }}
        
        .nav-pills .nav-link {{
            border-radius: 25px;
            margin: 0 5px;
            transition: all 0.3s ease;
        }}
        
        .nav-pills .nav-link.active {{
            background: linear-gradient(135deg, #3498db, #2980b9);
        }}
        
        .nav-pills .nav-link:hover {{
            background-color: #e9ecef;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 20px 0;
        }}
        
        .loading {{
            text-align: center;
            padding: 50px;
            color: #6c757d;
        }}
        
        .related-jobs {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
        }}
        
        .job-card {{
            background: white;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="dashboard-container">
            <div class="header">
                <h1><i class="fas fa-chart-line"></i> Job Market Analysis Dashboard</h1>
                <p class="lead">Comprehensive insights for career planning and development</p>
                <small class="text-muted">Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</small>
            </div>
            
            <!-- Statistics Overview -->
            <div class="row">
                <div class="col-md-3">
                    <div class="stats-card">
                        <i class="fas fa-chart-bar fa-2x mb-3"></i>
                        <h3>{len(self.dashboard_data)}</h3>
                        <p>Total Analyses</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card" style="background: linear-gradient(135deg, #e74c3c, #c0392b);">
                        <i class="fas fa-cogs fa-2x mb-3"></i>
                        <h3>{sum(analysis['count'] for analysis in self.dashboard_data.values())}</h3>
                        <p>Total Records</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card" style="background: linear-gradient(135deg, #27ae60, #229954);">
                        <i class="fas fa-briefcase fa-2x mb-3"></i>
                        <h3>15</h3>
                        <p>Analysis Types</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stats-card" style="background: linear-gradient(135deg, #f39c12, #e67e22);">
                        <i class="fas fa-users fa-2x mb-3"></i>
                        <h3>∞</h3>
                        <p>Student Benefits</p>
                    </div>
                </div>
            </div>
            
            <!-- Navigation -->
            <ul class="nav nav-pills justify-content-center my-4" id="analysisTab" role="tablist">'''
        
        # Add navigation tabs
        for i, (key, analysis) in enumerate(self.dashboard_data.items()):
            active_class = "active" if i == 0 else ""
            html_content += f'''
                <li class="nav-item" role="presentation">
                    <button class="nav-link {active_class}" id="{key}-tab" data-bs-toggle="pill" 
                            data-bs-target="#{key}" type="button" role="tab">
                        {analysis['title'][:20]}{'...' if len(analysis['title']) > 20 else ''}
                    </button>
                </li>'''
        
        html_content += '''
            </ul>
            
            <!-- Tab Content -->
            <div class="tab-content" id="analysisTabContent">'''
        
        # Add content for each analysis
        for i, (key, analysis) in enumerate(self.dashboard_data.items()):
            active_class = "show active" if i == 0 else ""
            
            html_content += f'''
                <div class="tab-pane fade {active_class}" id="{key}" role="tabpanel">
                    <div class="analysis-section">
                        <h2 class="analysis-title">
                            <i class="fas fa-chart-pie"></i> {analysis['title']}
                        </h2>
                        <p class="text-muted">Found {analysis['count']} records in this analysis</p>
                        
                        <div class="data-table">
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>'''
            
            # Add table headers based on the first record
            if analysis['data']:
                first_record = analysis['data'][0]
                for column in first_record.keys():
                    if column not in ['id', 'analysis_date', 'related_jobs']:
                        column_name = column.replace('_', ' ').title()
                        html_content += f'<th>{column_name}</th>'
                html_content += '<th>Related Jobs</th>'
            
            html_content += '''
                                        </tr>
                                    </thead>
                                    <tbody>'''
            
            # Add table rows (limit to top 20 for display)
            for record in analysis['data'][:20]:
                html_content += '<tr>'
                
                for column, value in record.items():
                    if column not in ['id', 'analysis_date', 'related_jobs']:
                        # Format values based on type
                        if isinstance(value, float):
                            if 'salary' in column.lower():
                                formatted_value = f"{value/100000:.1f} LPA" if value > 100000 else f"₹{value:,.0f}"
                            elif 'percentage' in column.lower() or 'rate' in column.lower():
                                formatted_value = f"{value:.1f}%"
                            else:
                                formatted_value = f"{value:.2f}"
                        elif isinstance(value, int) and value > 1000:
                            formatted_value = f"{value:,}"
                        else:
                            formatted_value = str(value)[:50] + ('...' if len(str(value)) > 50 else '')
                        
                        html_content += f'<td>{formatted_value}</td>'
                
                # Add related jobs
                related_jobs_html = ''
                try:
                    if record.get('related_jobs'):
                        related_jobs = json.loads(record['related_jobs'])
                        if related_jobs:
                            related_jobs_html = f'''
                                <button class="btn btn-sm btn-outline-primary" type="button" 
                                        data-bs-toggle="collapse" data-bs-target="#jobs_{record['id']}"
                                        aria-expanded="false">
                                    View {len(related_jobs)} Jobs
                                </button>
                                <div class="collapse mt-2" id="jobs_{record['id']}">
                                    <div class="related-jobs">'''
                            
                            for job in related_jobs[:3]:  # Show top 3 jobs
                                related_jobs_html += f'''
                                    <div class="job-card">
                                        <strong>{job.get('title', 'N/A')}</strong><br>
                                        <small class="text-muted">
                                            {job.get('company', 'N/A')} • {job.get('location', 'N/A')} • {job.get('salary', 'N/A')}
                                        </small>
                                    </div>'''
                            
                            related_jobs_html += '</div></div>'
                        else:
                            related_jobs_html = '<span class="text-muted">No jobs available</span>'
                    else:
                        related_jobs_html = '<span class="text-muted">No jobs available</span>'
                except:
                    related_jobs_html = '<span class="text-muted">No jobs available</span>'
                
                html_content += f'<td>{related_jobs_html}</td></tr>'
            
            html_content += '''
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>'''
        
        html_content += '''
            </div>
            
            <!-- Footer -->
            <div class="text-center mt-5 pt-4 border-top">
                <p class="text-muted">
                    <i class="fas fa-database"></i> 
                    Data updated in real-time from job market analysis • 
                    <i class="fas fa-users"></i> 
                    Designed for student career guidance
                </p>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Add smooth scrolling and enhanced interactions
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize tooltips
            var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
            
            // Add loading states
            $('.nav-link').on('click', function() {
                var target = $(this).data('bs-target');
                $(target).find('.analysis-section').addClass('loading');
                setTimeout(function() {
                    $(target).find('.analysis-section').removeClass('loading');
                }, 500);
            });
            
            console.log('Job Analysis Dashboard loaded successfully!');
        });
    </script>
</body>
</html>'''
        
        # Save HTML file
        with open('job_analysis_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✓ Generated beautiful HTML dashboard: job_analysis_dashboard.html")
    
    def run_dashboard_generation(self):
        \"\"\"Main function to generate the dashboard\"\"\"
        print("🚀 Starting Dashboard Generation...")
        print("="*50)
        
        if not self.connect_database():
            return False
        
        try:
            # Extract all data
            print("\\n📊 Extracting analysis data...")
            self.extract_all_analysis_data()
            
            if not self.dashboard_data:
                print("❌ No analysis data found. Please run the analyses first.")
                return False
            
            # Export to JSON
            print("\\n💾 Exporting data to JSON...")
            self.export_data_to_json()
            
            # Generate HTML dashboard
            print("\\n🌐 Generating HTML dashboard...")
            self.generate_html_dashboard()
            
            print("\\n" + "="*50)
            print("✅ Dashboard Generation Complete!")
            print("="*50)
            print("\\n📁 Files created:")
            print("  • job_analysis_dashboard.html - Beautiful web dashboard")
            print("  • dashboard_data.json - Raw data export")
            print("\\n🌐 Open job_analysis_dashboard.html in your browser to view the dashboard")
            
            return True
            
        except Exception as e:
            print(f"❌ Dashboard generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.close_database()

def main():
    \"\"\"Main function\"\"\"
    dashboard = JobAnalysisDashboard()
    dashboard.run_dashboard_generation()

if __name__ == "__main__":
    main()
"""

# Save the web dashboard generator
with open('web_dashboard_generator.py', 'w') as f:
    f.write(web_dashboard_content)

print("✓ Created comprehensive web_dashboard_generator.py")