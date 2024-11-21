# Importer les bibliothèques nécessaires
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Charger Sentence-BERT
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

# Poids des critères
WEIGHTS = {
    "education": 15,
    "experience": 20,
    "languages": 10,
    "technical_skills": 20,
    "soft_skills": 20,
    "availability": 10,
    "location": 5,
    "job_description": 5,
}

# Fonctions (inchangées)
def semantic_similarity(text1, text2, model):
    if not text1 or not text2:
        return 0.0
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)
    return cosine_similarity([emb1], [emb2])[0][0]

def compare_education(candidate_level, candidate_degree, job_level):
    candidate_text = f"{candidate_level} {candidate_degree}" if candidate_level != "missing" else "missing"
    return semantic_similarity(candidate_text, job_level, sbert_model)

def calculate_experience_score(candidate_years, required_years):
    if required_years == "not_required":
        return 1.0
    required_years = float(required_years)
    candidate_years = float(candidate_years) if candidate_years != "missing" else 0
    return min(candidate_years / required_years, 1.0)

def calculate_language_score(candidate_languages, candidate_levels, job_languages, job_levels):
    candidate_languages = eval(candidate_languages) if candidate_languages != "missing" else []
    candidate_levels = eval(candidate_levels) if candidate_levels != "missing" else []
    job_languages = eval(job_languages) if job_languages != "missing" else []
    job_levels = eval(job_levels) if job_levels != "missing" else []

    score = 0
    total_required = len(job_languages)
    for lang, level in zip(job_languages, job_levels):
        if lang in candidate_languages:
            idx = candidate_languages.index(lang)
            if candidate_levels[idx] == level:
                score += 1
    return score / total_required if total_required > 0 else 1

def calculate_skills_score(candidate_skills, job_skills):
    return semantic_similarity(candidate_skills, job_skills, sbert_model)

def location_score(candidate_location, job_location):
    geolocator = Nominatim(user_agent="geoapi")
    try:
        candidate_coords = geolocator.geocode(candidate_location)
        job_coords = geolocator.geocode(job_location)
        if candidate_coords and job_coords:
            dist = geodesic((candidate_coords.latitude, candidate_coords.longitude),
                            (job_coords.latitude, job_coords.longitude)).kilometers
            if dist < 50:  # Même ville
                return 1
            elif dist < 200:  # Même région
                return 0.8
            elif dist < 1000:  # Même pays
                return 0.6
            elif dist < 3000:  # Pays voisins
                return 0.4
            else:  # Même continent
                return 0.2
    except:
        return 0
    return 0

def calculate_job_description_score(candidate_position, job_title, job_profile):
    title_score = semantic_similarity(candidate_position, job_title, sbert_model)
    profile_score = semantic_similarity(candidate_position, job_profile, sbert_model)
    return (title_score + profile_score) / 2

def calculate_global_score(candidate, job):
    scores = {}
    max_scores = WEIGHTS  # Les poids sont les scores max pour chaque critère

    # Education
    scores["education"] = abs(compare_education(
        candidate["education_level"], candidate["education_degree"], job["education_level"]
    ) * WEIGHTS["education"])

    # Experience
    scores["experience"] = abs(calculate_experience_score(
        candidate["experience_years"], job["experience_years"]
    ) * WEIGHTS["experience"])

    # Languages
    scores["languages"] = abs(calculate_language_score(
        candidate["language"], candidate["language_level"], job["languages"], job["language_level"]
    ) * WEIGHTS["languages"])

    # Technical Skills
    scores["technical_skills"] = abs(calculate_skills_score(
        candidate["technical_skills"], job["technical_skills"]
    ) * WEIGHTS["technical_skills"])

    # Soft Skills
    scores["soft_skills"] = abs(calculate_skills_score(
        f"{candidate['soft_skills']} {candidate['hobbies']} {candidate['volunteer_activities']}",
        job["soft_skills"]
    ) * WEIGHTS["soft_skills"])

    # Availability (utilise `availability` pour les candidats et `start_date` pour les offres)
    scores["availability"] = abs((1 if candidate["availability"] == job["start_date"] else 0) * WEIGHTS["availability"])

    # Location
    scores["location"] = abs(location_score(candidate["location"], job["location"]) * WEIGHTS["location"])

    # Job Description
    scores["job_description"] = abs(calculate_job_description_score(
        candidate["current_position"], job["job_title"], job["profile"]
    ) * WEIGHTS["job_description"])

    # Score total
    # Convertir les scores en float
    for key in scores:
        if isinstance(scores[key], np.float32):
            scores[key] = float(scores[key])
    # Keep only four digits for each score
    for key in scores:
        scores[key] = round(scores[key], 2)

    # Create the same but normalize the values with the WEIGHTs
    normalize_scores = {key: round(value / WEIGHTS[key] *100, 2) for key, value in scores.items()}

    total_score = round(sum(scores.values()),2)
    return scores, normalize_scores, total_score

# Exemple d'utilisation avec les IDs
def get_scores_by_ids(candidate, job):
    # Pre-treatment to tranform list in string
    for column in ['technical_skills', 'soft_skills']:
        job[column] = ' '.join(job[column])
        candidate[column] = ' '.join(candidate[column])
    
    job['profile'] = ' '.join(job['profile'])

    if type(candidate['language']) == list:
        candidate['language'] = str(candidate['language'])
    if type(candidate['language_level']) == list:
        candidate['language_level'] = str(candidate['language_level'])

   
    detailed_scores, max_scores, global_score = calculate_global_score(candidate, job)
    return (global_score, detailed_scores, max_scores)
    ####
    #print(f"Scores pour le candidat {candidate_id} et l'offre {job_id} :")
    #for criterion, value in detailed_scores.items():
    #    print(f"{criterion.capitalize()} Score: {value:.2f} / {max_scores[criterion]:.2f}")
    #print(f"Global Score: {global_score:.2f} / 100.00")
    ####
    

# Exemple d'utilisation
#get_scores_by_ids(1, 1)