from flask import Blueprint, render_template, request, abort
import pandas as pd
import ast

main = Blueprint('main', __name__)

# Loda data
resumes = pd.read_csv('data/Resume.csv', header=0)
offers = pd.read_csv('data/final_job_offers.csv', header=0)
matches = pd.read_csv('data/matches.csv', header=0)

# Parse columns as a list if necessary
columns_to_parse = ['job_category','profile','education_speciality','languages','language_level','soft_skills','technical_skills','certifications','platform']
for column in columns_to_parse:
    offers[column] = offers[column].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
    )
# Parse 'details' column in matches as a list if necessary
matches['details'] = matches['details'].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
)

# Replace NaN values 
offers = offers.fillna({'education_level': 'Not specified', 'location': 'Not specified', 'start_date': 'Not specified', 'experience_years':0})

@main.route('/')
def home():
    return render_template('dashboard.html', data_summary=resumes.describe().to_html())

# Charger vos CSV en mémoire au démarrage
cv_data = pd.read_csv('data/final_candidates_merged.csv')  # Fichier CSV contenant les informations sur les CVs
job_offer_data = pd.read_csv('data/final_job_offers.csv')  # Fichier CSV contenant les informations sur les offres d'emploi

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

@main.route('/chart', methods=['GET', 'POST'])
def chart():
    if request.method == 'POST':
        # Récupérez les IDs envoyés par le formulaire
        cv_id = request.form.get('cv_id')
        job_offer_id = request.form.get('job_offer_id')

        # Calculer les statistiques
        stats = get_statistics(cv_id, job_offer_id)

        # Si une erreur existe, renvoyer l'erreur
        if "error" in stats:
            return jsonify(stats), 400

        return jsonify(stats)

    return render_template('chart.html')

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
    # Fetch job-related resumes from the dataframe
    relevant_resumes = matches[matches['id_offer'] == job_id]
    # Sort by global score and select top 5
    top_resumes = relevant_resumes.sort_values(by='score', ascending=False).head(10)
    
    # Convert to dictionary format for easier rendering in the template
    top_resumes = top_resumes.to_dict(orient='records')

    # Generate thresholds for score visualization
    thresholds = {
        "Excellent": 90,
        "Great": 75,
        "Good": 60,
        "Bad": 0
    }

    # Add a short snippet of the HTML (strip tags for text preview)
    resume_ids = [resume['id_resume'] for resume in top_resumes]
    resume_details = resumes[resumes['ID'].isin(resume_ids)][['ID', 'Resume_str']].set_index('ID').to_dict(orient='index')
    
    # Add the resume details to the top_resumes
    for resume in top_resumes:
        resume_id = resume['id_resume']
        if resume_id in resume_details:
            resume['snippet'] = resume_details[resume_id]['Resume_str'][:150] + '...'  # First 150 characters of the str
        # Find the resume details in the resumes DataFrame
        else:
            resume['snippet'] = ''

    # Example ranges for each detail (0-20, 0-10, etc.)
    detail_ranges = [20, 10, 15, 10, 5, 20, 10, 10]  # Adjust based on your use case
    normalized_resumes = normalize_details(top_resumes, detail_ranges)    
    return render_template(
        'job_analysis.html',
        num_details=len(detail_ranges),
        job_id=job_id,
        resumes=normalized_resumes,
        thresholds=thresholds
    )

def normalize_details(resumes, detail_ranges):
    """
    Normalize the scores of resumes based on the ranges for each detail.
    Args:
        resumes: List of resumes with details scores.
        detail_ranges: List of maximum values for each detail.
    Returns:
        Normalized resumes with details scaled between 0 and 1.
    """
    for resume in resumes:
        resume['normalized_details'] = [
            (score / max_range) * 100 if max_range > 0 else 0
            for score, max_range in zip(resume['details'], detail_ranges)
        ]
    return resumes