from flask import Blueprint, render_template, request, abort
import pandas as pd
import ast

main = Blueprint('main', __name__)

# Loda data
resumes = pd.read_csv('data/Resume.csv', header=0)
offers = pd.read_csv('data/final_job_offers.csv', header=0)

# Parse columns as a list if necessary
columns_to_parse = ['job_category','profile','education_speciality','languages','language_level','soft_skills','technical_skills','certifications','platform']
for column in columns_to_parse:
    offers[column] = offers[column].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
    )

# Replace NaN values 
offers = offers.fillna({'education_level': 'Not specified', 'location': 'Not specified', 'start_date': 'Not specified', 'experience_years':0})

@main.route('/')
def home():
    return render_template('dashboard.html', data_summary=resumes.describe().to_html())

@main.route('/chart')
def chart():
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

