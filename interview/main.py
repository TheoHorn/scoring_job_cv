import streamlit as st
import os

# Page de sélection initiale
st.title("Bienvenue dans l'outil d'entretien interactif")

st.write("Veuillez choisir une option pour commencer :")

# Bouton pour s'entraîner
if st.button("S'entraîner pour un entretien"):
    st.write("Redirection vers l'application d'entraînement...")
    # Lancer app.py
    os.system("streamlit run app.py")

# Bouton pour passer un entretien
if st.button("Passer un entretien"):
    st.write("Redirection vers l'application d'entretien réel...")
    # Lancer app1.py
    os.system("streamlit run app1.py")
