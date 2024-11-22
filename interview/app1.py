#Génère juste les questions sans des phrases au début pour les présenter sans rien d'autres juste les questions.
#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
import streamlit as st
import openai
import PyPDF2

# Configuration de l'API OpenAI
openai.api_key = "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"  # Remplacez par votre clé OpenAI

# Fonction pour extraire le texte d'un PDF
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Fonction pour générer des questions avec OpenAI
def generate_questions(cv_text, job_offer_text, type_interview="RH"):
    if type_interview == "RH":
        prompt = f"""
        Voici un CV et une offre d'emploi. 
        - CV : {cv_text[:1500]}...
        - Offre : {job_offer_text[:1000]}...

        Génère 10 questions adaptées pour un entretien RH. Éloigne-toi des questions techniques ici, génère plutôt des questions sur le parcours, le meilleur projet, la motivation, la disponibilité géographique, les langues maîtrisées, ce qu'on cherche comme environnement de travail, si le poste proposé intéresse le candidat. Génère juste les questions sans phrases au début pour les présenter, rien d'autre que les questions.
        """
    else:
        prompt = f"""
        Voici un CV et une offre d'emploi. 
        - CV : {cv_text[:1500]}...
        - Offre : {job_offer_text[:1000]}...

        Génère 10 questions adaptées pour un entretien technique, très techniques. Les questions doivent être spécifiques pour évaluer les compétences nécessaires à l'offre. Génère juste les questions sans phrases au début pour les présenter, rien d'autre que les questions.
        """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Tu es un assistant spécialisé en création de questionnaires d'entretien."},
            {"role": "user", "content": prompt},
        ],
    )
    return response["choices"][0]["message"]["content"]

# Fonction pour nettoyer les questions générées
def clean_questions(questions_text):
    """
    Nettoie et formate les questions générées en supprimant les lignes vides.
    """
    return [q.strip() for q in questions_text.split("\n") if q.strip()]

# Fonction pour générer un feedback basé sur les réponses
def evaluate_responses(questions, answers, type_interview="RH"):
    """
    Génère un feedback basé sur les réponses fournies.
    Si aucune réponse n'est donnée, retourne un message indiquant que le questionnaire n'a pas été rempli.
    """
    # Vérifier si toutes les réponses sont vides
    if all(not answer.strip() for answer in answers):
        return "Le candidat n'a pas répondu aux questions."

    # Générer le prompt pour l'API
    if type_interview == "RH":
        prompt = f"""
        Voici les questions d'entretien RH et les réponses fournies par un candidat :
        
        Questions :
        {questions}
        
        Réponses du candidat :
        {answers}
        
        Fournis un feedback détaillé :
        1. Les points forts du candidat.
        2. Les points faibles.
        3. À quel point le profil correspond à l'offre.
        4. Une évaluation de la motivation dégagée à travers les réponses.
        """
    else:
        prompt = f"""
        Voici les questions d'entretien technique et les réponses fournies par un candidat :
        
        Questions :
        {questions}
        
        Réponses du candidat :
        {answers}
        
        Fournis un feedback détaillé :
        1. Les compétences techniques démontrées.
        2. Les lacunes ou axes d'amélioration.
        3. Une évaluation générale des compétences par rapport aux exigences de l'offre.
        """
    
    # Appeler l'API OpenAI pour générer le feedback
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Tu es un expert en évaluation des réponses d'entretien."},
            {"role": "user", "content": prompt},
        ],
    )
    return response["choices"][0]["message"]["content"]

# Fonction pour réinitialiser l'état de l'application
def reset_state():
    keys_to_reset = ["cv_text", "job_offer_text", "rh_questions", "tech_questions", "rh_feedback", "tech_feedback"]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

# Navigation entre les étapes
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "upload"

def change_page(page_name):
    st.session_state["current_page"] = page_name
    if page_name == "upload":
        reset_state()

# Étape 1 : Chargement du CV et de l'offre
if st.session_state["current_page"] == "upload":
    st.title("Étape 1 : Chargement des documents")
    uploaded_file = st.file_uploader("Glissez votre CV ici (PDF uniquement)", type="pdf")
    job_offer_text = st.text_area("Collez l'offre d'emploi ici")

    if uploaded_file and job_offer_text:
        cv_text = extract_text_from_pdf(uploaded_file)
        st.session_state["cv_text"] = cv_text
        st.session_state["job_offer_text"] = job_offer_text
        st.success("CV et offre d'emploi chargés avec succès.")
        if st.button("Commencer l'entretien RH"):
            change_page("interview_rh")

# Étape 2 : Interview RH
elif st.session_state["current_page"] == "interview_rh":
    st.title("Étape 2 : Interview RH")
    if "rh_questions" not in st.session_state:
        raw_questions = generate_questions(
            st.session_state["cv_text"], st.session_state["job_offer_text"], "RH"
        )
        st.session_state["rh_questions"] = clean_questions(raw_questions)

    questions = st.session_state["rh_questions"]
    st.write("Répondez aux questions suivantes :")

    answers = []
    for i, question in enumerate(questions, start=1):
        st.markdown(f"**{i}. {question}**")
        answer = st.text_area(f"Votre réponse à la question {i} :", key=f"rh_answer_{i}")
        answers.append(answer)

    if st.button("Terminer l'entretien RH"):
        feedback = evaluate_responses("\n".join(questions), "\n".join(answers), "RH")
        st.session_state["rh_feedback"] = feedback
        change_page("rh_feedback")

# Étape 3 : Feedback RH
elif st.session_state["current_page"] == "rh_feedback":
    st.title("Feedback de l'entretien RH")
    st.write(st.session_state.get("rh_feedback", "Feedback indisponible."))
    if st.button("Passer à l'entretien technique"):
        change_page("interview_technique")

# Étape 4 : Interview technique
elif st.session_state["current_page"] == "interview_technique":
    st.title("Étape 4 : Interview technique")
    if "tech_questions" not in st.session_state:
        raw_questions = generate_questions(
            st.session_state["cv_text"], st.session_state["job_offer_text"], "technique"
        )
        st.session_state["tech_questions"] = clean_questions(raw_questions)

    questions = st.session_state["tech_questions"]
    st.write("Répondez aux questions suivantes :")

    answers = []
    for i, question in enumerate(questions, start=1):
        st.markdown(f"**{i}. {question}**")
        answer = st.text_area(f"Votre réponse à la question {i} :", key=f"tech_answer_{i}")
        answers.append(answer)

    if st.button("Terminer l'entretien technique"):
        feedback = evaluate_responses("\n".join(questions), "\n".join(answers), "technique")
        st.session_state["tech_feedback"] = feedback
        change_page("tech_feedback")

# Étape 5 : Feedback technique
elif st.session_state["current_page"] == "tech_feedback":
    st.title("Feedback de l'entretien technique")
    st.write(st.session_state.get("tech_feedback", "Feedback indisponible."))
    if st.button("Revenir à l'accueil"):
        change_page("upload")
