from flask import Blueprint, render_template, request, abort, jsonify, redirect, url_for
import pandas as pd
import numpy as np
import ast
import os 
#import cohere
import openai
import json
import reimport 
import re
import app.logic.notation as notation
import json

main = Blueprint('main', __name__)

def handle_missing_values(data, is_candidate):
    for column in data.columns:
        data[column] = data[column].apply(lambda x: "missing" if x in ["", "[]", None, np.nan] else x)
        if is_candidate:
            # Si c'est un candidat, les valeurs manquantes comptent comme un désavantage
            data[column].fillna("missing", inplace=True)
        else:
          # Si c'est une offre, les valeurs manquantes indiquent que ce critère est optionnel
            data[column].fillna("not_required", inplace=True)
    return data

# Loda data
resumes = pd.read_csv('data/Resume.csv', header=0)
candidates = pd.read_csv('data/final_candidates_merged.csv', header=0)
offers = pd.read_csv('data/final_job_offers.csv', header=0)
matches = pd.read_csv('data/matches.csv', header=0)

candidates = handle_missing_values(candidates, is_candidate=True)
offers = handle_missing_values(offers, is_candidate=False)

# Parse columns as a list if necessary
columns_to_parse = ['job_category','profile','education_speciality','languages','language_level','soft_skills','technical_skills','certifications','platform']
for column in columns_to_parse:
    offers[column] = offers[column].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
    )

columns_to_parse = ['education_speciality', 'language', 'language_level', 'technical_skills', 'soft_skills', 'location_available', 'certifications_title', 'hobbies', 'volunteer_activities', 'school_projects']
for column in columns_to_parse:
    candidates[column] = candidates[column].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
    )

# Parse 'details' column in matches as a list if necessary
matches['details'] = matches['details'].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
)


# Charger vos CSV en mémoire au démarrage
cv_data = candidates  # Fichier CSV contenant les informations sur les CVs
job_offer_data = offers # Fichier CSV contenant les informations sur les offres d'emploi

# Exemple de fonction pour calculer des statistiques à partir des CSVs
def get_statistics(cv_id, job_offer_id):
    # Filtrer les lignes correspondant aux IDs donnés
    cv = cv_data[cv_data['id'] == int(cv_id)]
    job_offer = job_offer_data[job_offer_data['id'] == int(job_offer_id)]

    # Vérifiez si les données existent
    if cv.empty or job_offer.empty:
        return {"error": "CV ID or Job Offer ID not found."}

    # Simuler des calculs basés sur vos données
    skills_match = len(set(cv['skills'].values[0].split(',')) & set(job_offer['skills_required'].values[0].split(',')))
    experience_overlap = abs(cv['years_experience'].values[0] - job_offer['min_experience'].values[0])
    education_match = int(cv['education_level'].values[0] == job_offer['education_required'].values[0])
    industry_relevance = len(set(cv['industries'].values[0].split(',')) & set(job_offer['industries_targeted'].values[0].split(',')))

    # Retourner les statistiques calculées
    return {
        "skills_match": skills_match,
        "experience_overlap": experience_overlap,
        "education_match": education_match,
        "industry_relevance": industry_relevance
    }

@main.route('/')
def home():
    return render_template('home.html', data_summary=resumes.describe().to_html())

@main.route('/resumes')
def list_resumes():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)  # Default to page 1
    per_page = 25  # Number of resumes per page

    selected_category = request.args.get('category')  # Selected category filter

    # Filter DataFrame by category (if selected)
    if selected_category:
        filtered_df = resumes[resumes['Category'] == selected_category]
    else:
        filtered_df = resumes
    
    # Calculate start and end indices
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Slice the DataFrame
    total_resumes = len(filtered_df)
    current_page_resumes = filtered_df.iloc[start_idx:end_idx][['ID', 'Category', 'Resume_str']].to_dict(orient='records')
    
    # Add a short snippet of the HTML (strip tags for text preview)
    for resume in current_page_resumes:
        resume['snippet'] = resume['Resume_str'][:150] + '...'  # First 150 characters of the HTML
    
    # Get unique categories for filter dropdown
    categories = resumes['Category'].unique().tolist()
    categories.sort()  # Sort alphabetically

    # Calculate total pages
    total_pages = (total_resumes + per_page - 1) // per_page  # Round up division
    
    return render_template(
        'resumes.html', 
        resumes=current_page_resumes, 
        page=page, 
        categories=categories,
        selected_category=selected_category,
        total_pages=total_pages
    )

from PyPDF2 import PdfReader

#API_KEY = "PnKSZ7AFasSX81TgZWgASYdIyypiInXdghzZh4g4"
#co = cohere.Client(API_KEY)


OPENAI_API_KEY = "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"  
openai.api_key = OPENAI_API_KEY

from werkzeug.utils import secure_filename
from io import BytesIO

# Fonction pour nettoyer la réponse de Cohere
def clean_response(response_text):
    response_text = response_text.strip()

    # Rechercher la partie JSON valide
    json_match = re.search(r"{.*}", response_text, re.DOTALL)

    if not json_match:
        print("Aucun JSON valide trouvé dans la réponse brute.")
        return None

    # Extraire uniquement le JSON
    json_text = json_match.group()

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"Erreur de décodage JSON : {e}")
        return None

def analyze_cv_with_openai(cv_text, candidate_id):
    prompt = f"""
    You are an expert CV analyzer. Analyze the following CV text and extract relevant details to create a structured dataset for job matching.

    Extract the following details:
    - Candidate ID: The unique identifier of the candidate should be an integer.
    - Education School: Name of the schools or institutions.
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
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional CV analyzer."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    raw_text = response["choices"][0]["message"]["content"].strip()
    return clean_response(raw_text)

# Function to check if a value is invalid
def is_invalid(value):
    if value is None or isinstance(value, (list, str)) and not value:  # Handle empty lists and empty strings
        return True
    invalid_values = {"n/a", "none", "not specified", "not mentionned", "missing"}
    return str(value).strip().lower() in invalid_values
# Ajouter un CV à la table
def add_cv_to_table(cv_text, table_path):
    global resumes
    # Vérifier si le fichier existe
    if os.path.exists(table_path):
        df = pd.read_csv(table_path)
        next_id = df["candidate_id"].max() + 1
    else:
        print(f"{table_path} n'existe pas. Création d'une nouvelle table.")
        next_id = 1
        columns = [
            "candidate_id", "education_school", "education_speciality", "education_level",
            "education_degree", "experience_years", "language", "language_level",
            "technical_skills", "soft_skills", "current_position", "location",
            "location_available", "certifications_title", "hobbies", "volunteer_activities",
            "school_projects", "availability"
        ]
        df = pd.DataFrame(columns=columns)

    # Découper le CV en morceaux
    cv_chunks = [cv_text[i:i+2000] for i in range(0, len(cv_text), 2000)]

    # Analyser chaque morceau du CV
    results = []
    for chunk in cv_chunks:
        response_raw = analyze_cv_with_openai(chunk, candidate_id=next_id)
        if response_raw:
            results.append(response_raw)

    # Fusionner les résultats si nécessaire
    if results:
        merged_result = {key: value for d in results for key, value in d.items()}
        df = pd.concat([df, pd.DataFrame([merged_result])], ignore_index=True)

    # Sauvegarder le fichier mis à jour
    df_final = pd.concat([df, pd.DataFrame([merged_result])], ignore_index=True)

    # Sauvegarder le fichier mis à jour
    df_final.to_csv(table_path, index=False)
    df_final = pd.read_csv('data/final_candidates_merged.csv', header=0)

    new_html = f"""<div class="resume" id="resume-{next_id}">
    """

    df_resume = pd.DataFrame([{'ID': next_id, 'Resume_html': new_html,'Category': "missing"}])
    new_res= pd.concat([resumes, df_resume], ignore_index=True)
    new_res.to_csv('data/Resume.csv', index=False)
    resumes = new_res

# Route to handle the matching page and PDF upload
@main.route('/score', methods=['GET', 'POST'])
def score():
    global candidates
    result = None
    if request.method == 'POST':
        # Get the uploaded PDF file
        pdf_file = request.files['pdf']
        if pdf_file:
            # Read the PDF and extract text
            pdf_path = pdf_file.filename
            reader = PdfReader(pdf_file)
            cv_text = ""
            for page in reader.pages:
                cv_text += page.extract_text()

            # Add the CV to the table
            table_path = 'data/final_candidates_merged.csv'  # Update with actual path
            add_cv_to_table(cv_text, table_path)

            # Analyze the CV using Cohere API
            candidate_id = candidates['candidate_id'].max()
            result = analyze_cv_with_openai(cv_text, candidate_id)

            candidates = pd.read_csv('data/final_candidates_merged.csv', header=0)
    
    visible = request.method == 'POST'  # Determine if the result should be displayed
        # Render the page with the extracted data
    print(result)
    return render_template('score.html', result=result, visible=visible)

def analyze_job_offer_with_openai(offer_text, job_id):
    """
    Analyse une offre d'emploi à l'aide d'OpenAI et retourne un résultat structuré en JSON.
    """
    prompt = f"""
    You are an expert job posting analyzer. Your task is to analyze the following job posting and extract relevant details to create a structured dataset for matching with candidate resumes.

    Extract the following details:
    - Job ID: Unique identifier for the job posting.
    - Job Title: Full title of the job.
    - Job Category: Categorize the job into key domains such as "Data Science", "Healthcare", "Finance", etc.
    - Profile: List general profiles required (e.g., "Graduate Student", "Engineer", "Technician", "Manager").
    - Education Level: Minimum academic level required (e.g., "Bachelor's", "Master's", "PhD", "BUT", "DUT").
    - Education Speciality: Extract academic specialities explicitly mentioned or implied in the job posting. Only include existing and relevant fields of study (e.g., "Computer Science", "Marketing", "Data Science"). Avoid vague or non-academic terms.
    - Experience Years: Minimum number of years of experience required explicitly mentioned.
    - Languages: List languages required for the job explicitly mentioned.
    - Language Levels: Proficiency level for each language. It should be one of these: "Beginner", "Intermediate", "Advanced".
    - Start Date: Mention the start date or specify if it’s "Immediate" or "ASAP".
    - Soft Skills: List key soft skills required (e.g., "Teamwork", "Communication").
    - Technical Skills: List key technical skills required (e.g., "Python", "Cloud Computing").
    - Certifications: Extract recognized and standard professional certifications explicitly mentioned in the job posting. Include certifications like "AWS Certified Solutions Architect", "PMP Certification". Ignore generic terms or unverified certifications.
    - Location: Job location in "City, State, Country" format.

    Job Information: {offer_text}

    Provide the output in this JSON format:
    {{
        "job_id": "{job_id}",
        "job_title": "value",
        "job_category": ["category1", "category2", ...],
        "profile": ["profile1", "profile2", ...],
        "education_level": "value",
        "education_speciality": ["speciality1", "speciality2", ...],
        "experience_years": number,
        "languages": ["language1", "language2", ...],
        "language_level": ["level1", "level2", ...],
        "start_date": "value",
        "soft_skills": ["soft_skill1", "soft_skill2", ...],
        "technical_skills": ["technical_skill1", "technical_skill2", ...],
        "certifications": ["certification1", "certification2", ...],
        "location": "City, State, Country"
    }}
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional job posting analyzer."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    raw_text = response["choices"][0]["message"]["content"].strip()
    return clean_response(raw_text)

# Add job offer to the CSV table (same as you already implemented)
def add_job_offer_to_table(offer_text, table_path):
    global offers
    if os.path.exists(table_path):
        df = pd.read_csv(table_path)
        # S'assurer que "job_id" est de type entier
        if not df.empty and "job_id" in df.columns:
            df["job_id"] = pd.to_numeric(df["job_id"], errors="coerce").fillna(0).astype(int)
            next_id = df["job_id"].max() + 1
        else:
            next_id = 1
    else:
        print(f"{table_path} does not exist. Creating a new table.")
        next_id = 1
        columns = [
            "job_id", "job_title", "job_category", "profile", "education_level",
            "education_speciality", "experience_years", "languages", "language_level",
            "start_date", "soft_skills", "technical_skills", "certifications", "location"
        ]
        df = pd.DataFrame(columns=columns)

    # Simule l'analyse avec une fonction "analyze_job_offer_with_cohere"
    response_raw = analyze_job_offer_with_openai(offer_text, job_id=next_id)

    # Ajouter les nouvelles données à la table
    df = pd.concat([df, pd.DataFrame([response_raw])], ignore_index=True)
    df.to_csv(table_path, index=False)
    print(f"Job offer successfully added to {table_path}.")

    offers = pd.read_csv('data/final_job_offers.csv', header=0)

# Route to show the offer submission form
@main.route('/offers', methods=['GET', 'POST'])
def offers_view():
    return render_template('offers.html')

# Route to handle the form submission and add job offer to the CSV
@main.route('/add_offer', methods=['POST'])
def add_offer():
    file = request.files.get('file')

    if file :
        # Ajouter l'offre au fichier CSV sans avoir besoin d'extraction manuelle
        table_path = 'data/final_job_offers.csv'
        # Tu peux directement envoyer un texte d'offre vide (ou autre traitement si nécessaire)
        add_job_offer_to_table(file, table_path)

        # Rediriger vers la page des offres après l'ajout
        return redirect(url_for('main.offers_view'))

    return render_template('offers.html', error="Only PDF files are allowed.")  # Afficher une erreur si ce n'est pas un PDF

@main.route('/resumes/<int:resume_id>')
def view_resume(resume_id):
    # Filter the DataFrame to find the resume by ID
    resume = resumes[resumes['ID'] == resume_id].to_dict(orient='records')
    resume_row = resumes[resumes['ID'] == resume_id]
    print(resume)
    if resume_row.empty:
        candidate = candidates[candidates['candidate_id'] == resume_id].to_dict(orient='records')
        
        if candidate:
            # Iterate through each record (as it's a list of dictionaries)
            for record in candidate:
                # Iterate through each key-value pair in the dictionary
                for key, value in record.items():
                    # If the value is a list, convert it to a string
                    if isinstance(value, list):
                        # Convert list to a comma-separated string (or any other format you prefer)
                        record[key] = ', '.join(map(str, value))
            ncandidate = candidate[0]
            resume_html = f"""<div class="cv-container">
                
                <div class="cv-header">
                    <h1>CV</h1> 
                    <p><strong>Location:</strong> {ncandidate['location']}</p>
                    <p><strong>Current Position:</strong> {ncandidate['current_position']}</p>
                </div>

                <!-- Education Section -->
                <div class="section-title">Education</div>
                <div class="section-content">
                    <p><strong>School:</strong> {ncandidate['education_school']}</p>
                    <p><strong>Speciality:</strong> {ncandidate['education_speciality']}</p>
                    <p><strong>Level:</strong> {ncandidate['education_level']}</p>
                    <p><strong>Degree:</strong> {ncandidate['education_degree']}</p>
                </div>

                <!-- Experience Section -->
                <div class="section-title">Experience</div>
                <div class="section-content">
                    <p><strong>Years of Experience:</strong> {ncandidate['experience_years']}</p>
                </div>

                <!-- Language Skills Section -->
                <div class="section-title">Language Skills</div>
                <div class="section-content">
                    <p><strong>Language:</strong> {ncandidate['language']}</p>
                    <p><strong>Level:</strong> {ncandidate['language_level']}</p>
                </div>

                <!-- Technical Skills Section -->
                <div class="section-title">Technical Skills</div>
                <div class="section-content">
                    <p>{ncandidate['technical_skills']}</p>
                </div>

                <!-- Soft Skills Section -->
                <div class="section-title">Soft Skills</div>
                <div class="section-content">
                    <p>{ncandidate['soft_skills']}</p>
                </div>

                <!-- Certifications Section -->
                <div class="section-title">Certifications</div>
                <div class="section-content">
                    <p>{ncandidate['certifications_title']}</p>
                </div>

                <!-- Hobbies Section -->
                <div class="section-title">Hobbies</div>
                <div class="section-content">
                    <p>{ncandidate['hobbies']}</p>
                </div>

                <!-- Volunteer Activities Section -->
                <div class="section-title">Volunteer Activities</div>
                <div class="section-content">
                    <p>{ncandidate['volunteer_activities']}</p>
                </div>

                <!-- School Projects Section -->
                <div class="section-title">School Projects</div>
                <div class="section-content">
                    <p>{ncandidate['school_projects']}</p>
                </div>

                <!-- Availability Section -->
                <div class="section-title">Availability</div>
                <div class="section-content">
                    <p>{ncandidate['availability']}</p>
                </div>

                <!-- CV Footer -->
                <div class="cv-footer">
                    <p>Candidate ID: {ncandidate['candidate_id']}</p>
                </div>
            </div>
            """
            resume_id = ncandidate['candidate_id']
            print(resume_id)
        else:
            abort(404)
    else:      
        # Extract the HTML representation
        resume_html = resume_row.iloc[0]['Resume_html']
        resume_id = resume_row.iloc[0]['ID']
    return render_template('resume.html', resume_html=resume_html,resume_id=resume_id)


@main.route('/resumes/<int:resume_id>/matching')
def matching_resumes(resume_id):
    # Run Notation.py functions to calculate scores for candidates not already in matches
    global matches
    resume = candidates[candidates['candidate_id'] == resume_id].iloc[0]
    if resume.empty:
        abort(404, description="Resume ID not analysed.")
    
    for _, offer in offers.tail(10).iterrows():
        if not matches[(matches['id_offer'] == offer['job_id']) & (matches['id_resume'] == resume_id)].empty:
            continue

        # Calculate the score for the candidate
        (score_global, detailled_scores, normalize_scores) = notation.get_scores_by_ids(resume, offer)

        # Append the new score to the matches DataFrame
        new_match = {
            'id_offer': offer['job_id'],
            'id_resume': resume_id,
            'score': score_global,
            'details': detailled_scores,
            'normalized': normalize_scores
        }

        matches = pd.concat([matches, pd.DataFrame([new_match])], ignore_index=True)

    # Save the updated matches DataFrame back to the CSV
    matches.to_csv('data/matches.csv', index=False)

    # Fetch resume-related jobs from the dataframe
    relevant_jobs = matches[matches['id_resume'] == resume_id]

    # Sort by global score and select top 5
    top_jobs = relevant_jobs.sort_values(by='score', ascending=False).head(10)

    # Convert to dictionary format for easier rendering in the template
    top_jobs = top_jobs.to_dict(orient='records')

    for job in top_jobs:
        if isinstance(job['normalized'], str):
            job['normalized'] = job['normalized'].replace("'", '"')
            try:
                job['normalized'] = json.loads(job['normalized'])
            except json.JSONDecodeError:
                job['normalized'] = {}
    
    print(top_jobs[0])
    return render_template(
        'resume_analysis.html',
        num_details=len(list(notation.WEIGHTS.values())),
        resume_id=resume_id,
        jobs=top_jobs,
        string_details=list(notation.WEIGHTS.keys())
    )


@main.route('/jobs')
def list_jobs():
    # Define relevant columns for the job list
    relevant_columns = ['job_id', 'job_title', 'job_category', 'location', 'experience_years', 'start_date']    
    filtered_jobs = offers[relevant_columns]

    # Get filter parameters from query string
    category_filter = request.args.get('category', '')
    location_filter = request.args.get('location', '')

    # Apply filters if provided
    if category_filter:
        filtered_jobs = filtered_jobs[filtered_jobs['job_category'].apply(lambda x: any(category_filter.lower() in cat.lower() for cat in x))]
    if location_filter:
        filtered_jobs = filtered_jobs[filtered_jobs['location'].str.contains(location_filter, case=False, na=False)]

    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 25
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Paginate results
    total_jobs = len(filtered_jobs)
    paginated_jobs = filtered_jobs.iloc[start_idx:end_idx].to_dict(orient='records')
    total_pages = (total_jobs + per_page - 1) // per_page

    # Convert job_category to a comma-separated string if it's a list
    for job in paginated_jobs:
        if isinstance(job['job_category'], list):
            job['job_category'] = ", ".join(job['job_category'])

    #if experience years == "not_required" then we show 0
    for job in paginated_jobs:
        if job['experience_years'] == "not_required":
            job['experience_years'] = 0

    return render_template(
        'jobs.html',
        jobs=paginated_jobs,
        page=page,
        total_pages=total_pages,
        category_filter=category_filter,
        location_filter=location_filter
    )


@main.route('/jobs/<int:job_id>')
def view_job(job_id):  
    # Filter the DataFrame for the selected job
    job = offers[offers['job_id'] == job_id].to_dict(orient='records')
    if not job:
        abort(404)  # Return a 404 if the job ID is not found

    # Extract the first (and only) record as a dictionary
    job = job[0]

    # Convert job_category and languages to comma-separated strings if they are lists
    for field in ['job_category','profile','education_speciality','languages','language_level','soft_skills','technical_skills','certifications','platform']:
        if isinstance(job[field], list):
            job[field] = ", ".join(job[field])

    return render_template('job.html', job=job)

@main.route('/jobs/<int:job_id>/matching')
def matching(job_id):
    # Run Notation.py functions to calculate scores for candidates not already in matches
    global matches
    offer = offers[offers['job_id'] == job_id].iloc[0]
    for _, candidate in candidates.tail(10).iterrows():
        if not matches[(matches['id_offer'] == job_id) & (matches['id_resume'] == candidate['candidate_id'])].empty:
            continue  # Skip if the candidate is already in the matches

        # Calculate the score for the candidate
        (score_global, detailled_scores, normalize_scores) = notation.get_scores_by_ids(candidate, offer)
        
        # Append the new score to the matches DataFrame
        new_match = {
            'id_offer': job_id,
            'id_resume': candidate['candidate_id'],
            'score': score_global,
            'details': detailled_scores,
            'normalized': normalize_scores
        }
        matches = pd.concat([matches, pd.DataFrame([new_match])], ignore_index=True)

    # Save the updated matches DataFrame back to the CSV
    matches.to_csv('data/matches.csv', index=False)

    # Fetch job-related resumes from the dataframe
    relevant_resumes = matches[matches['id_offer'] == job_id]

    # Sort by global score and select top 5
    top_resumes = relevant_resumes.sort_values(by='score', ascending=False).head(10)
    
    # Convert to dictionary format for easier rendering in the template
    top_resumes = top_resumes.to_dict(orient='records')
    print(top_resumes[5])
    
# Fixing the normalized string by replacing single quotes with double quotes
    for resume in top_resumes:
        if isinstance(resume['normalized'], str):
            resume['normalized'] = resume['normalized'].replace("'", '"')  # Replace single quotes with double quotes
            try:
                resume['normalized'] = json.loads(resume['normalized'])  # Convert string to dictionary
            except json.JSONDecodeError:
                resume['normalized'] = {}  # Handle cases where the JSON is malformed
                
    return render_template(
        'job_analysis.html',
        num_details=len(list(notation.WEIGHTS.values())),
        job_id=job_id,
        resumes=top_resumes,
        string_details=list(notation.WEIGHTS.keys())
    )
