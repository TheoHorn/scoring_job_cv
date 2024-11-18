# Return a csv file with the following columns: 
# - "skill" : list of skills
# - "experience" : list of experiences
# - "education" : list of educations
# - "languages" : list of languages
# - "Years of experience" : number of years of experience
# - "Dates" : disponibility dates
# - "Location" : location

### IMPORTS
import txt2data as txt2data
import pandas as pd
import re
### MAIN FUNCTION

# This function is used to parse a resume and extract some information from it
txt2data.main()

# Initialize a dictionary to store processed data
processed_data = {}

# Load the data
df = pd.read_csv('data/processed_resumes.csv')
for i in range(len(df)):
    resume_id = df.iloc[i]['ID']
    resume_skills = df.iloc[i]['skills']
    resume_experience = df.iloc[i]['experience']
    resume_education = df.iloc[i]['education']
    resume_languages = df.iloc[i]['languages']
    resume_summary = df.iloc[i]['summary']
    resume_accomplishments = df.iloc[i]['accomplishments']
    resume_projects = df.iloc[i]['projects']
    resume_certifications = df.iloc[i]['certifications']
    resume_interests = df.iloc[i]['interests']
    resume_publications = df.iloc[i]['publications']
    resume_overview = df.iloc[i]['overview']
    resume_qualifications = df.iloc[i]['qualifications']

    summary_info = resume_summary if pd.notna(resume_summary) else resume_overview

    # Extract years of experience
    experience_years = 0
    if pd.notna(summary_info):
        matches = re.findall(r'(\d+)\s?year?', summary_info)
        if matches:
            experience_years = int(matches[0])

    experience_years_exp = 0
    if pd.notna(resume_experience):
        matches = re.findall(r'(\d{6})', resume_experience)
        if matches:
            dates = []
            for match in matches:
                year = int(match[2:])
                month = int(match[0:2])
                date = year + month/12
                dates.append(year)
            if dates:
                experience_years_exp = max(dates) - min(dates)

    # Compare years of experience from summary and experience sections
    experience_years = max(experience_years, experience_years_exp)
        

    # Determine education information
    education_info = resume_education if pd.notna(resume_education) else resume_qualifications

    # Store the processed data
    processed_data[resume_id] = {
        'skill': resume_skills,
        'experience': resume_experience,
        'education': education_info,
        'languages': resume_languages,
        'Years of experience': experience_years,
        'Dates': '',  # Add logic to extract dates if needed
        'Location': ''  # Add logic to extract location if needed
    }

# Convert dictionary to a DataFrame for analysis or export
processed_df = pd.DataFrame.from_dict(processed_data, orient='index')

# Export the results to a CSV file
processed_df.to_csv('data/cv_analysed.csv', index_label='ID')