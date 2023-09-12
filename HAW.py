import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime

# Initialisation de la base de données
conn = sqlite3.connect('data.db')
c = conn.cursor()

# Initialisation de l'état de la session
if 'is_user_logged_in' not in st.session_state:
    st.session_state['is_user_logged_in'] = False

if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

# Création des tables
def create_tables():
    c.execute('CREATE TABLE IF NOT EXISTS articles(title TEXT, content TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS comments(article_title TEXT, comment TEXT, author TEXT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS members(username TEXT UNIQUE, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS documents(name TEXT, file BLOB)')
    c.execute('CREATE TABLE IF NOT EXISTS observations(observer TEXT, is_member TEXT, location TEXT, geo_location TEXT, type_of_aid TEXT, number_of_beneficiaries INTEGER, aid_amount REAL, comments TEXT, file_data BLOB, file_type TEXT, date TEXT)')
    conn.commit()

create_tables()

# Navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Aller à", ["Accueil---Observation", "Actualités", "Espace Membres", "Chatbot"])

# Page d'Accueil
if selection == "Accueil---Observation":
    st.title("Accueil---Observation")
    st.image("HAW-logo.png", width=300)
    st.write("""
    # Bienvenue sur Human Aid Watch (HAW)
    🌍Suivi transparent de la distribution de l'aide humanitaire.
    """)
# Formulaire d'observation
    st.subheader("Ajouter une observation --------------- ملاحظة")
    location = st.text_input("Lieu de l'observation --------------- موقع الملاحظة")
    geo_location = st.text_input("Géolocalisation (latitude, longitude) --------------- الموقع الجغرافي")
    type_of_aid = st.selectbox("Type d'aide --------------- نوع المساعدة", ["Nourriture", "Médicaments", "Vêtements", "Argent", "Travaux", "Autre"])
    number_of_beneficiaries = st.number_input("Nombre de bénéficiaires --------------- عدد المستفدين", min_value=1)
    aid_amount = st.number_input("Estimation du montant de l'aide reçue (en dirham) --------------- قيمة المساعدة", min_value=0.0, step=0.01)
    comments = st.text_area("Commentaire --------------- تعليق")


    uploaded_file = st.file_uploader("Choisissez une vidéo ou une photo à uploader", type=["mp4", "avi", "mov", "jpg", "png"])
    file_data = None
    file_type = None
    if uploaded_file:
        file_data = uploaded_file.read()
        file_type = uploaded_file.type

    observer = "Anonyme"
    is_member = "Non"
    if st.session_state['is_user_logged_in']:
        observer = st.session_state['current_user']
        is_member = "Oui"

    if st.button("Soumettre l'observation"):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO observations (observer, is_member, location, geo_location, type_of_aid, number_of_beneficiaries, aid_amount, comments, file_data, file_type, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (observer, is_member, location, geo_location, type_of_aid, number_of_beneficiaries, aid_amount, comments, file_data, file_type, current_time))
        conn.commit()
        st.write("Observation soumise avec succès.")

    # Afficher les dernières observations
    st.subheader("Dernières observations")
    latest_observations = pd.read_sql_query('SELECT * FROM observations ORDER BY date DESC LIMIT 5', conn)
    for i, row in latest_observations.iterrows():
        st.markdown(f"---")
        st.write(f"Observateur: {row['observer']}")
        st.write(f"Lieu: {row['location']}")
        st.write(f"Type d'aide: {row['type_of_aid']}")
        st.write(f"Nombre de bénéficiaires: {row['number_of_beneficiaries']}")
        st.write(f"Montant de l'aide: {row['aid_amount']}")
        st.write(f"Commentaires: {row['comments']}")
        st.write(f"Date: {row['date']}")

# Page d'Actualités
elif selection == "Actualités":
    st.title("Actualités")

    # Afficher les articles
    articles = pd.read_sql_query('SELECT * FROM articles', conn)
    for i, row in articles.iterrows():
        st.subheader(row['title'])
        st.markdown(f"### {row['content']}")

        # Commentaires
        st.markdown("---")
        st.write("Commentaires:")
        comments = pd.read_sql_query(f"SELECT * FROM comments WHERE article_title='{row['title']}'", conn)
        for _, comment_row in comments.iterrows():
            st.markdown(f"--- *{comment_row['comment']}*")
            st.markdown(f"Écrit par **{comment_row['author']}** le {comment_row['date']}")

        # Ajouter un commentaire (si connecté)
        if st.session_state['is_user_logged_in']:
            new_comment = st.text_input(f"Ajouter un commentaire pour {row['title']}")
            if st.button(f"Publier le commentaire pour {row['title']}"):
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO comments (article_title, comment, author, date) VALUES (?, ?, ?, ?)",
                        (row['title'], new_comment, st.session_state['current_user'], current_time))
                conn.commit()
                st.write("Commentaire ajouté.")

# Page Espace Membres
elif selection == "Espace Membres":
    st.title("Espace Membres")

    if not st.session_state['is_user_logged_in']:
        account_option = st.selectbox("Avez-vous déjà un compte ?", ["Oui", "Non"])
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")

        if account_option == "Oui":
            if st.button("Se connecter"):
                # Vérification des identifiants
                saved_password = c.execute("SELECT password FROM members WHERE username=?", (username,)).fetchone()
                if saved_password and bcrypt.checkpw(password.encode('utf-8'), saved_password[0].encode('utf-8')):
                    st.write("Connexion réussie. Bienvenue!")
                    st.session_state['is_user_logged_in'] = True
                    st.session_state['current_user'] = username
                
        else:
            if st.button("S'inscrire"):
                # Création d'un nouveau compte
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                try:
                    c.execute("INSERT INTO members (username, password) VALUES (?, ?)", (username, hashed_password))
                    conn.commit()
                    st.write("Compte créé avec succès. Vous pouvez maintenant vous connecter.")
                except sqlite3.IntegrityError:
                    st.write("Ce nom d'utilisateur est déjà pris.")
    else:
        st.write(f"Bienvenue, {st.session_state['current_user']}")

        # Bouton de déconnexion
        if st.button("Se déconnecter"):
            st.session_state['is_user_logged_in'] = False
            st.session_state['current_user'] = None
            st.write("Vous avez été déconnecté.")
            st.experimental_rerun()

# Page Chatbot
elif selection == "Chatbot":
    st.title("Assistant")
    st.write("Posez vos questions ici.")
    user_input = st.text_input("Votre question")
    if user_input:
        st.write("Réponse de l'assistant.")

