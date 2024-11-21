import pandas as pd
import os
import cohere
import json
import re

# Configuration for Cohere
API_KEY = "mOn7gI1TUOROkDHm202ZdZSs4bvdAFZscSPLPd67"  # Replace with your actual Cohere API key
co = cohere.Client(API_KEY)

# Clean the raw response from Cohere
def clean_response(response_text):
    response_text = response_text.strip()

    # Search for valid JSON in the response
    json_match = re.search(r"{.*}", response_text, re.DOTALL)

    if not json_match:
        print("No valid JSON found in the raw response.")
        return {
            "candidate_id": None,
            "education_school": None,
            "education_speciality": [],
            "education_level": None,
            "education_degree": None,
            "experience_years": None,
            "language": [],
            "language_level": [],
            "technical_skills": [],
            "soft_skills": [],
            "current_position": None,
            "location": None,
            "location_available": [],
            "certifications_title": [],
            "hobbies": [],
            "volunteer_activities": [],
            "school_projects": [],
            "availability": None,
        }

    # Extract only the JSON part
    json_text = json_match.group()

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return {
            "candidate_id": None,
            "education_school": None,
            "education_speciality": [],
            "education_level": None,
            "education_degree": None,
            "experience_years": None,
            "language": [],
            "language_level": [],
            "technical_skills": [],
            "soft_skills": [],
            "current_position": None,
            "location": None,
            "location_available": [],
            "certifications_title": [],
            "hobbies": [],
            "volunteer_activities": [],
            "school_projects": [],
            "availability": None,
        }

# Analyze CV text with Cohere
def analyze_cv_with_cohere(cv_text, candidate_id):
    prompt = f"""
    You are an expert CV analyzer. Analyze the following CV text and extract relevant details to create a structured dataset for job matching.

    Extract the following details:
    - Candidate ID: The unique identifier of the candidate.
    - Education School: Name of the school or institution.
    - Education Speciality: Fields of study (e.g., "Computer Science", "Marketing").
    - Education Level: Academic level completed (e.g., "Bachelor's", "Master's", "PhD").
    - Education Degree: Name of the degree (e.g., "Master of Science", "Bachelor of Arts").
    - Experience Years: Number of years of professional experience.
    - Language: List of languages known.
    - Language Level: Proficiency level for each language (e.g., "Beginner", "Intermediate", "Advanced").
    - Technical Skills: List of technical skills mentioned in the CV.
    - Soft Skills: List of soft skills mentioned in the CV.
    - Current Position: Current job title (if mentioned).
    - Location: Current location of the candidate.
    - Location Available: List of locations the candidate is willing to work in.
    - Certifications Title: Titles of certifications obtained.
    - Hobbies: Hobbies or personal interests.
    - Volunteer Activities: List of volunteer or extracurricular activities.
    - School Projects: List of academic projects completed.
    - Availability: Candidate's availability for a new role (e.g., "Immediate", "1 month notice").

    CV Text: {cv_text}

    Provide the output in this JSON format:
    {{
        "candidate_id": "{candidate_id}",
        "education_school": "value",
        "education_speciality": ["speciality1", "speciality2", ...],
        "education_level": "value",
        "education_degree": "value",
        "experience_years": number,
        "language": ["language1", "language2", ...],
        "language_level": ["level1", "level2", ...],
        "technical_skills": ["skill1", "skill2", ...],
        "soft_skills": ["soft_skill1", "soft_skill2", ...],
        "current_position": "value",
        "location": "City, State, Country",
        "location_available": ["City1, State1, Country1", ...],
        "certifications_title": ["certification1", "certification2", ...],
        "hobbies": ["hobby1", "hobby2", ...],
        "volunteer_activities": ["activity1", "activity2", ...],
        "school_projects": ["project1", "project2", ...],
        "availability": "value"
    }}
    """
    response = co.generate(
        model="command-xlarge-nightly",
        prompt=prompt,
        max_tokens=500,
        temperature=0.7
    )
    raw_text = response.generations[0].text.strip()
    return clean_response(raw_text)

# Add CV to an existing table or create a new one
def add_cv_to_table(cv_text, table_path):
    # Check if the file exists
    if os.path.exists(table_path):
        df = pd.read_csv(table_path)
        next_id = df["candidate_id"].max() + 1
    else:
        print(f"{table_path} does not exist. Creating a new table.")
        next_id = 1
        columns = [
            "candidate_id", "education_school", "education_speciality", "education_level",
            "education_degree", "experience_years", "language", "language_level",
            "technical_skills", "soft_skills", "current_position", "location",
            "location_available", "certifications_title", "hobbies", "volunteer_activities",
            "school_projects", "availability"
        ]
        df = pd.DataFrame(columns=columns)

    # Analyze the CV
    response_raw = analyze_cv_with_cohere(cv_text, candidate_id=next_id)

    # Add the CV data to the DataFrame
    df = pd.concat([df, pd.DataFrame([response_raw])], ignore_index=True)

    # Save the updated file
    df.to_csv(table_path, index=False)
    print(f"The CV has been successfully added to {table_path}.")
