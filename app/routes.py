from flask import Blueprint, render_template, request, abort
import pandas as pd

main = Blueprint('main', __name__)

# Charger les données
resumes = pd.read_csv('data/Resume.csv')

@main.route('/')
def home():
    return render_template('dashboard.html', data_summary=resumes.describe().to_html())

@main.route('/chart')
def chart():
    return render_template('chart.html')

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