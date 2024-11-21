from flask import Blueprint, render_template, request, abort
import pandas as pd
import numpy as np
import ast
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
    return render_template('dashboard.html', data_summary=resumes.describe().to_html())

@main.route('/chart', methods=['POST'])
def chart():
    try:
        # Get IDs from the request
        cv_id = int(request.form['cv_id'])
        job_offer_id = int(request.form['job_offer_id'])

        # Fetch the corresponding rows
        candidate = candidates_df[candidates_df['candidate_id'] == cv_id].iloc[0]
        job = job_offers_df[job_offers_df['job_id'] == job_offer_id].iloc[0]

        # Calculate scores
        detailed_scores, max_scores, global_score = calculate_global_score(candidate, job)

        # Structure the data for the frontend
        response_data = {
            "skills_match": detailed_scores["technical_skills"],
            "experience_overlap": detailed_scores["experience"],
            "education_match": detailed_scores["education"],
            "industry_relevance": detailed_scores["job_description"],
            "global_score": global_score,
        }

        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

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


@main.route('/resumes/<int:resume_id>')
def view_resume(resume_id):
    # Filter the DataFrame to find the resume by ID
    resume_row = resumes[resumes['ID'] == resume_id]
    if resume_row.empty:
        abort(404)  # Return a 404 error if no match is found
    
    # Extract the HTML representation
    resume_html = resume_row.iloc[0]['Resume_html']
    return render_template('resume.html', resume_html=resume_html)


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
    for _, candidate in candidates.head(10).iterrows():
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
