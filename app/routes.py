from flask import Blueprint, render_template, request, abort
import pandas as pd

main = Blueprint('main', __name__)

# Charger les données
resumes = pd.read_csv('data/Resume.csv', header=0)

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
    per_page = 20  # Number of resumes per page

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


#@main.route('/offer/{id}')
#def offer():
#    return render_template('offer.html', offer=df.iloc[id])