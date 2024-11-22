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

# Fonction pour générer un questionnaire avec OpenAI
def generate_questionnaire(cv_text, job_offer_text, type_interview="RH"):
    if type_interview == "RH":
        prompt = f"""
        Voici un CV et une offre d'emploi. 
        - CV : {cv_text[:1500]}... 
        - Offre : {job_offer_text[:1000]}...

        Génère un questionnaire de 10 questions pour un entretien RH. Les questions doivent être adaptées au profil du candidat et à l'offre d'emploi. Fournis également une réponse simulée pour chaque question.
        """
    else:
        prompt = f"""
        Voici un CV et une offre d'emploi. 
        - CV : {cv_text[:1500]}...
        - Offre : {job_offer_text[:1000]}...

        Génère un questionnaire de 10 questions pour un entretien technique selon l'offre.Le but de ces questions est de s'assurer que le candidat a les compétences et connaissances techniques requises pour le poste. Les questions doivent être techniques et alignées avec les compétences requises pour l'offre. Fournis également une réponse simulée pour chaque question.
        """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Tu es un assistant spécialisé en génération de questionnaires d'entretien."},
            {"role": "user", "content": prompt},
        ],
    )
    return response["choices"][0]["message"]["content"]

# Fonction pour réinitialiser l'état de la session
def reset_state():
    keys_to_reset = ["cv_text", "job_offer_text", "rh_questions", "tech_questions"]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

# Initialiser l'état de la page
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "upload"  # Par défaut, page de chargement du CV

# Fonction pour passer à une autre page
def change_page(page_name):
    st.session_state["current_page"] = page_name
    if page_name == "upload":
        reset_state()

# Page : Chargement du CV et de l'offre
if st.session_state["current_page"] == "upload":
    st.title("Étape 1 : Chargement des documents")
    uploaded_file = st.file_uploader("Glissez votre CV ici (PDF uniquement)", type="pdf")
    job_offer_text = st.text_area("Collez l'offre d'emploi ici")

    if uploaded_file and job_offer_text:
        cv_text = extract_text_from_pdf(uploaded_file)
        st.session_state["cv_text"] = cv_text
        st.session_state["job_offer_text"] = job_offer_text
        st.success("CV et offre d'emploi chargés avec succès.")
        if st.button("Passer à l'interview RH"):
            change_page("interview_rh")

# Page : Interview RH
elif st.session_state["current_page"] == "interview_rh":
    st.title("Étape 2 : Interview RH")
    if "rh_questions" not in st.session_state:
        rh_questions = generate_questionnaire(
            st.session_state["cv_text"], st.session_state["job_offer_text"], type_interview="RH"
        )
        st.session_state["rh_questions"] = rh_questions

    st.write(st.session_state["rh_questions"])
    if st.button("Passer à l'interview technique"):
        change_page("interview_technique")

# Page : Interview technique
elif st.session_state["current_page"] == "interview_technique":
    st.title("Étape 3 : Interview technique")
    if "tech_questions" not in st.session_state:
        tech_questions = generate_questionnaire(
            st.session_state["cv_text"], st.session_state["job_offer_text"], type_interview="technique"
        )
        st.session_state["tech_questions"] = tech_questions

    st.write(st.session_state["tech_questions"])
    if st.button("Revenir à l'accueil"):
        change_page("upload")
