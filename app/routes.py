from flask import Blueprint, render_template, request
import pandas as pd

main = Blueprint('main', __name__)

# Charger les données
df = pd.read_csv('data/Resume.csv')

@main.route('/')
def home():
    return render_template('dashboard.html', data_summary=df.describe().to_html())

@main.route('/chart')
def chart():
    return render_template('chart.html')
