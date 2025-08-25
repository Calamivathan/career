#!/usr/bin/env python3
"""
Salary and Data Parsing Utilities
Handles proper extraction and normalization of salary and other data fields
"""

import re
import json
from typing import Optional, Dict, Any

class SalaryParser:
    """Handles parsing salary from both salary and salary_detail fields"""

    @staticmethod
    def extract_salary_value(salary_text: str = None, salary_detail: str = None) -> Optional[float]:
        """
        Extract numeric salary value from text or JSON salary_detail
        Returns salary in INR (actual amount, not LPA)
        """
        # First try salary_detail JSON if available
        if salary_detail:
            try:
                if isinstance(salary_detail, str):
                    salary_json = json.loads(salary_detail)
                else:
                    salary_json = salary_detail

                min_salary = salary_json.get('minimumSalary', 0)
                max_salary = salary_json.get('maximumSalary', 0)

                # If both are valid, take average
                if min_salary > 0 and max_salary > 0:
                    return (min_salary + max_salary) / 2
                elif min_salary > 0:
                    return min_salary
                elif max_salary > 0:
                    return max_salary
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        # Fall back to parsing salary text
        if not salary_text or str(salary_text).lower() in ['not disclosed', 'as per market standards', 'unpaid']:
            return None

        salary_str = str(salary_text).lower().replace(',', '').replace(' ', '')

        # Extract numbers
        numbers = re.findall(r'\d+(?:\.\d+)?', salary_str)
        if not numbers:
            return None

        # Handle ranges (e.g., "7-17 Lacs PA")
        if len(numbers) >= 2 and any(sep in salary_str for sep in ['-', 'to']):
            salary_value = (float(numbers[0]) + float(numbers[1])) / 2
        else:
            salary_value = float(numbers[0])

        # Convert based on units
        if any(unit in salary_str for unit in ['lpa', 'per annum', 'pa', 'annually']):
            return salary_value * 100000  # Convert LPA to actual amount
        elif 'crore' in salary_str:
            return salary_value * 10000000
        elif any(unit in salary_str for unit in ['lakh', 'lac']):
            return salary_value * 100000
        elif '/month' in salary_str or 'per month' in salary_str:
            return salary_value * 12  # Convert monthly to annual
        elif 'k' in salary_str and salary_value < 1000:
            return salary_value * 1000
        elif salary_value > 100000:  # Already in actual amount
            return salary_value
        elif salary_value > 1000:  # Assume thousands
            return salary_value * 1000
        else:
            # For small numbers, assume LPA
            return salary_value * 100000

class SkillsExtractor:
    """Handles extraction and cleaning of skills from text"""

    @staticmethod
    def extract_skills_from_text(text: str) -> list:
        """Extract and clean skills from tags_and_skills or job_description"""
        if not text:
            return []

        # Common skill separators
        skills = []

        # Split by various delimiters
        parts = re.split(r'[,;|\n\r\t]', str(text))

        for part in parts:
            skill = part.strip()

            # Clean and validate skill
            if skill and len(skill) > 1:
                # Remove common noise words
                noise_words = ['and', 'or', 'with', 'in', 'of', 'for', 'to', 'the', 'a', 'an']
                skill_clean = ' '.join([word for word in skill.split() 
                                     if word.lower() not in noise_words])

                # Limit skill length to prevent database errors
                if len(skill_clean) > 100:
                    skill_clean = skill_clean[:100] + '...'

                # Only add meaningful skills
                if len(skill_clean) > 2 and len(skill_clean.split()) <= 5:
                    skills.append(skill_clean.title())

        # Remove duplicates while preserving order
        unique_skills = []
        seen = set()
        for skill in skills:
            if skill.lower() not in seen:
                unique_skills.append(skill)
                seen.add(skill.lower())

        return unique_skills

class ExperienceParser:
    """Handles parsing experience requirements"""

    @staticmethod
    def extract_experience_range(min_exp: str = None, max_exp: str = None, 
                               exp_text: str = None) -> Dict[str, float]:
        """Extract min and max experience values"""
        result = {'min_experience': 0.0, 'max_experience': 0.0}

        # Try to parse min_exp and max_exp first
        try:
            if min_exp is not None:
                result['min_experience'] = float(min_exp)
        except (ValueError, TypeError):
            pass

        try:
            if max_exp is not None:
                result['max_experience'] = float(max_exp)
        except (ValueError, TypeError):
            pass

        # If we have both, we're done
        if result['min_experience'] > 0 and result['max_experience'] > 0:
            return result

        # Parse from experience text
        if exp_text:
            exp_str = str(exp_text).lower()

            # Look for patterns like "3+ years", "2-5 years", "0-1 yrs"
            patterns = [
                r'(\d+)\+',  # "3+"
                r'(\d+)-(\d+)',  # "2-5"
                r'(\d+)\s*(?:to|-)\s*(\d+)',  # "2 to 5"
                r'(\d+)',  # Single number
            ]

            for pattern in patterns:
                matches = re.findall(pattern, exp_str)
                if matches:
                    if len(matches[0]) == 2:  # Range pattern
                        result['min_experience'] = float(matches[0][0])
                        result['max_experience'] = float(matches[0][1])
                    else:  # Single number or "+"
                        exp_val = float(matches[0])
                        if '+' in exp_str:
                            result['min_experience'] = exp_val
                            result['max_experience'] = exp_val + 5  # Assume +5 for "+"
                        else:
                            result['min_experience'] = exp_val
                            result['max_experience'] = exp_val
                    break

        return result

class LocationNormalizer:
    """Handles location normalization"""

    @staticmethod
    def normalize_location(location: str) -> str:
        """Normalize location names to standard city names"""
        if not location:
            return "Unknown"

        location_str = str(location).strip()

        # Handle hybrid/remote locations
        if 'hybrid' in location_str.lower():
            # Extract city from "Hybrid - Bengaluru"
            match = re.search(r'hybrid\s*-\s*([^,()]+)', location_str, re.IGNORECASE)
            if match:
                location_str = match.group(1).strip()

        # Handle multiple locations - take the first one
        if ',' in location_str:
            location_str = location_str.split(',')[0].strip()

        # Handle locations with additional info in parentheses
        location_str = re.sub(r'\([^)]*\)', '', location_str).strip()

        # City mappings for consistency
        city_mappings = {
            'bengaluru': 'Bangalore',
            'bangalore': 'Bangalore',
            'mumbai': 'Mumbai',
            'pune': 'Pune',
            'delhi': 'Delhi',
            'new delhi': 'Delhi',
            'gurgaon': 'Gurgaon',
            'gurugram': 'Gurgaon',
            'hyderabad': 'Hyderabad',
            'chennai': 'Chennai',
            'kolkata': 'Kolkata',
            'ahmedabad': 'Ahmedabad',
            'noida': 'Noida',
            'kochi': 'Kochi',
            'cochin': 'Kochi',
            'thiruvananthapuram': 'Thiruvananthapuram',
            'coimbatore': 'Coimbatore',
            'indore': 'Indore',
            'jaipur': 'Jaipur',
            'lucknow': 'Lucknow',
            'chandigarh': 'Chandigarh',
            'bhubaneswar': 'Bhubaneswar',
            'patna': 'Patna',
            'surat': 'Surat',
            'vadodara': 'Vadodara'
        }

        location_lower = location_str.lower()
        for key, value in city_mappings.items():
            if key in location_lower:
                return value

        # Return title case if not found in mappings
        return location_str.title() if len(location_str) > 2 else "Unknown"

# Convenience functions
def parse_salary(salary_text=None, salary_detail=None):
    """Convenience function for salary parsing"""
    return SalaryParser.extract_salary_value(salary_text, salary_detail)

def extract_skills(text):
    """Convenience function for skills extraction"""
    return SkillsExtractor.extract_skills_from_text(text)

def parse_experience(min_exp=None, max_exp=None, exp_text=None):
    """Convenience function for experience parsing"""
    return ExperienceParser.extract_experience_range(min_exp, max_exp, exp_text)

def normalize_location(location):
    """Convenience function for location normalization"""
    return LocationNormalizer.normalize_location(location)
