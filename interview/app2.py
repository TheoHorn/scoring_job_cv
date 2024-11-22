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
def generate_questions(cv_text, job_offer_text, type_interview="RH", mode="train"):
    if mode == "train":
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

            Génère un questionnaire de 10 questions pour un entretien technique selon l'offre. Fournis également une réponse simulée pour chaque question.
            """
    else:  # Mode réel
        if type_interview == "RH":
            prompt = f"""
            Voici un CV et une offre d'emploi. 
            - CV : {cv_text[:1500]}...
            - Offre : {job_offer_text[:1000]}...

            Génère 10 questions adaptées pour un entretien RH. Éloigne-toi des questions techniques ici, génère plutôt des questions sur le parcours, la motivation, et l'intérêt pour le poste. Génère juste les questions sans phrases au début pour les présenter.
            """
        else:
            prompt = f"""
            Voici un CV et une offre d'emploi. 
            - CV : {cv_text[:1500]}...
            - Offre : {job_offer_text[:1000]}...

            Génère 10 questions adaptées pour un entretien technique. Les questions doivent être très techniques pour évaluer les compétences nécessaires à l'offre. Génère juste les questions sans phrases au début pour les présenter.
            """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Tu es un assistant spécialisé en création de questionnaires d'entretien."},
            {"role": "user", "content": prompt},
        ],
    )
    return response["choices"][0]["message"]["content"]

# Fonction pour réinitialiser l'état
def reset_state():
    keys_to_reset = ["cv_text", "job_offer_text", "rh_questions", "tech_questions", "mode"]
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

# Étape 1 : Chargement du CV et choix du mode
if st.session_state["current_page"] == "upload":
    st.title("Étape 1 : Chargement des documents et choix du mode")
    uploaded_file = st.file_uploader("Glissez votre CV ici (PDF uniquement)", type="pdf")
    job_offer_text = st.text_area("Collez l'offre d'emploi ici")

    if uploaded_file and job_offer_text:
        cv_text = extract_text_from_pdf(uploaded_file)
        st.session_state["cv_text"] = cv_text
        st.session_state["job_offer_text"] = job_offer_text
        st.success("CV et offre d'emploi chargés avec succès.")
        if st.button("S'entraîner pour l'entretien"):
            st.session_state["mode"] = "train"
            change_page("interview_rh")
        elif st.button("Passer l'entretien"):
            st.session_state["mode"] = "real"
            change_page("interview_rh")

# Étape 2 : Interview RH
elif st.session_state["current_page"] == "interview_rh":
    st.title("Étape 2 : Interview RH")
    if "rh_questions" not in st.session_state:
        rh_questions = generate_questions(
            st.session_state["cv_text"], 
            st.session_state["job_offer_text"], 
            type_interview="RH", 
            mode=st.session_state["mode"]
        )
        st.session_state["rh_questions"] = rh_questions

    st.write(st.session_state["rh_questions"])
    if st.button("Passer à l'interview technique"):
        change_page("interview_technique")

# Étape 3 : Interview technique
elif st.session_state["current_page"] == "interview_technique":
    st.title("Étape 3 : Interview technique")
    if "tech_questions" not in st.session_state:
        tech_questions = generate_questions(
            st.session_state["cv_text"], 
            st.session_state["job_offer_text"], 
            type_interview="technique", 
            mode=st.session_state["mode"]
        )
        st.session_state["tech_questions"] = tech_questions

    st.write(st.session_state["tech_questions"])
    if st.session_state["mode"] == "real":
        st.markdown("Répondez aux questions ci-dessus dans la zone prévue pour chaque question.")
        for i, question in enumerate(st.session_state["tech_questions"].split("\n"), start=1):
            st.text_area(f"Votre réponse à la question {i}", key=f"tech_answer_{i}")
    if st.button("Revenir à l'accueil"):
        change_page("upload")
