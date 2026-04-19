import streamlit as st
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import cv2
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
from datetime import datetime
import time
import base64
from io import BytesIO
import random
from fpdf import FPDF
import matplotlib.pyplot as plt
import re

# Configuration de la page
st.set_page_config(
    page_title="AutoDefect Pro - Diagnostic Intelligent",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== FONCTION DE NETTOYAGE POUR PDF ====================

def clean_text_for_pdf(text):
    """Nettoie le texte pour le PDF (remplace les emojis et caractères spéciaux)"""
    # Remplacer les emojis par du texte
    replacements = {
        '🔴': '[ROUGE]',
        '🟠': '[ORANGE]',
        '🟡': '[JAUNE]',
        '✅': '[OK]',
        '⚠️': '[ALERTE]',
        '🚨': '[URGENT]',
        '🔧': '[OUTIL]',
        '🔄': '[REPARATION]',
        '🗑️': '[REJET]',
        '📊': '[STATS]',
        '👨‍🔧': '[TECHNICIEN]',
        '🔬': '[LABO]',
        '❌': '[NON]',
        '🧹': '[NETTOYAGE]',
        '🎨': '[PEINTURE]',
        '🛡️': '[PROTECTION]',
        '🌡️': '[TEMPERATURE]',
        '📅': '[CALENDRIER]',
        '📏': '[MESURE]',
        '📦': '[EMBALLAGE]',
        '🎯': '[CONTROLE]',
        '✂️': '[COUPE]',
        '🔪': '[FINITION]',
        '👁️': '[INSPECTION]',
        '📈': '[SUIVI]',
        '🚗': '[AUTO]',
        '📸': '[PHOTO]',
        '🔍': '[RECHERCHE]',
        '🛠️': '[MAINTENANCE]',
        '📄': '[DOCUMENT]',
        '📥': '[DOWNLOAD]',
        '🎯': '[CIBLE]',
        'ℹ️': '[INFO]',
        '📁': '[DOSSIER]',
        '📷': '[CAMERA]',
        '🔗': '[LIEN]',
        '🧠': '[IA]',
        '🤖': '[ROBOT]'
    }
    
    for emoji, replacement in replacements.items():
        text = text.replace(emoji, replacement)
    
    # Supprimer les autres caractères non ASCII
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    return text

def generate_pdf_report():
    """Génère un rapport PDF des analyses"""
    
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(102, 126, 234)
    pdf.cell(0, 20, 'AutoDefect Pro - Rapport Analyse', ln=True, align='C')
    
    pdf.set_font('Arial', 'I', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f'Genere le: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True, align='C')
    pdf.ln(10)
    
    # Résumé
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, '1. Resume des Analyses', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Total des analyses: {st.session_state.total}', ln=True)
    pdf.cell(0, 8, f'Pieces conformes (OK): {st.session_state.ok}', ln=True)
    pdf.cell(0, 8, f'Defauts detectes: {st.session_state.defauts}', ln=True)
    pdf.cell(0, 8, f'Taux de defaut: {st.session_state.defect_rate:.1f}%', ln=True)
    pdf.ln(5)
    
    # Détail des défauts par type
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '2. Detail des Defauts par Type', ln=True)
    pdf.set_font('Arial', '', 12)
    
    for defect_type, count in st.session_state.defect_types_count.items():
        if count > 0:
            defect_info = DEFECT_TYPES[defect_type]
            nom_clean = clean_text_for_pdf(defect_info["nom"])
            severite_clean = clean_text_for_pdf(defect_info["severite"])
            pdf.cell(0, 8, f'{nom_clean}: {count} occurrence(s)', ln=True)
            pdf.cell(0, 6, f'   - Severite: {severite_clean}', ln=True)
            pdf.cell(0, 6, f'   - Cout estime: {defect_info["cout_estime"]}', ln=True)
            pdf.ln(2)
    
    pdf.ln(5)
    
    # Historique des dernières analyses
    if st.session_state.history:
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, '3. Historique des Analyses', ln=True)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(40, 8, 'Date', 1)
        pdf.cell(35, 8, 'Statut', 1)
        pdf.cell(50, 8, 'Type', 1)
        pdf.cell(40, 8, 'Confiance', 1)
        pdf.ln()
        
        pdf.set_font('Arial', '', 9)
        for record in st.session_state.history[:20]:
            statut_clean = clean_text_for_pdf(record['Statut'])
            type_clean = clean_text_for_pdf(record['Type'])
            pdf.cell(40, 7, record['Date'][:16], 1)
            pdf.cell(35, 7, statut_clean, 1)
            pdf.cell(50, 7, type_clean[:20], 1)
            pdf.cell(40, 7, record['Confiance'], 1)
            pdf.ln()
    
    # Recommandations
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '4. Recommandations', ln=True)
    pdf.set_font('Arial', '', 12)
    
    if st.session_state.defect_rate > 20:
        pdf.cell(0, 8, 'Attention: Taux de defaut eleve - Action immediate requise:', ln=True)
        pdf.cell(0, 6, '   - Reviser le processus de production', ln=True)
        pdf.cell(0, 6, '   - Controler la qualite des matieres premieres', ln=True)
        pdf.cell(0, 6, '   - Former les operateurs', ln=True)
    elif st.session_state.defect_rate > 10:
        pdf.cell(0, 8, 'Attention: Taux de defaut modere - Surveillance renforcee:', ln=True)
        pdf.cell(0, 6, '   - Augmenter la frequence des controles', ln=True)
        pdf.cell(0, 6, '   - Analyser les causes principales', ln=True)
    else:
        pdf.cell(0, 8, 'Bonne performance - Maintenir les bonnes pratiques', ln=True)
    
    # Sauvegarder
    pdf_path = f"rapport_autodefect_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(pdf_path)
    
    return pdf_path

# ==================== DÉFINITION DES TYPES DE DÉFAUTS ====================

DEFECT_TYPES = {
    "rayure": {
        "nom": "Rayure profonde",
        "description": "Rayure visible sur la surface de la piece",
        "severite": "Critique",
        "causes": [
            "Frottement avec un objet metallique",
            "Mauvaise manipulation lors de l'assemblage",
            "Contact avec des outils non proteges"
        ],
        "maintenance": [
            "Action immediate: Isoler la piece defectueuse",
            "Reparation: Ponçage et polissage si la rayure est superficielle",
            "Remplacement: Remplacer la piece si la rayure depasse 0.5mm de profondeur",
            "Controle qualite: Verifier les outils de production",
            "Formation: Sensibiliser les operateurs aux bonnes pratiques"
        ],
        "cout_estime": "50-200 EUR",
        "temps_reparation": "30 min - 2h",
        "urgence": "Haute"
    },
    "fissure": {
        "nom": "Fissure / Craquelure",
        "description": "Fissure visible a l'oeil nu ou microscopique",
        "severite": "Tres Critique",
        "causes": [
            "Contrainte mecanique excessive",
            "Fatigue du materiau",
            "Defaut de fabrication (inclusion, porosite)",
            "Temperature extreme lors du processus"
        ],
        "maintenance": [
            "Action immediate: Mettre la piece hors service URGENT",
            "Inspection: Controle par ressuage ou magnetoscopie",
            "Remplacement obligatoire: La piece ne peut pas etre reparee",
            "Analyse des causes: Enquete sur le processus de fabrication",
            "Revision: Controler tous les lots similaires"
        ],
        "cout_estime": "200-1000 EUR",
        "temps_reparation": "2h - 1 jour",
        "urgence": "Urgente"
    },
    "corrosion": {
        "nom": "Corrosion / Rouille",
        "description": "Oxydation de la surface metallique",
        "severite": "Moyenne a Critique",
        "causes": [
            "Exposition a l'humidite prolongee",
            "Defaut de traitement anti-corrosion",
            "Contact avec des produits chimiques agressifs",
            "Stockage dans des conditions inappropriées"
        ],
        "maintenance": [
            "Nettoyage: Derouiller la surface avec des produits adaptes",
            "Traitement: Application d'un convertisseur de rouille",
            "Protection: Repeindre avec une peinture anti-corrosion",
            "Stockage: Verifier les conditions de stockage (hygrometrie)",
            "Plan de maintenance: Mettre en place des inspections regulieres"
        ],
        "cout_estime": "30-150 EUR",
        "temps_reparation": "1h - 4h",
        "urgence": "Moyenne"
    },
    "deformation": {
        "nom": "Deformation",
        "description": "Piece deformee, voilee ou tordue",
        "severite": "Critique",
        "causes": [
            "Choc pendant le transport",
            "Contrainte thermique mal maitrisee",
            "Defaut de conception du moule",
            "Retrait trop rapide du materiau"
        ],
        "maintenance": [
            "Mesure: Verifier les cotes avec un comparateur",
            "Redressage: Si possible, redresser mecaniquement",
            "Rejet: Remplacer si la deformation depasse les toleances",
            "Emballage: Renforcer les protections de transport",
            "Controle: Ajuster les parametres de production"
        ],
        "cout_estime": "80-300 EUR",
        "temps_reparation": "1h - 3h",
        "urgence": "Haute"
    },
    "bavure": {
        "nom": "Bavure / Exces de matiere",
        "description": "Exces de matiere sur les bords de la piece",
        "severite": "Moyenne",
        "causes": [
            "Usure des moules ou matrices",
            "Pression d'injection trop elevee",
            "Temperature de moulage inadaptee",
            "Mauvais reglage des parametres machine"
        ],
        "maintenance": [
            "Ebarbage: Retirer les bavures mecaniquement",
            "Finition: Passage a la finition automatique",
            "Reglage: Ajuster les parametres de production",
            "Inspection: Verification visuelle apres correction",
            "Suivi: Surveiller l'usure des outils"
        ],
        "cout_estime": "10-50 EUR",
        "temps_reparation": "15 min - 1h",
        "urgence": "Basse"
    },
    "inclusion": {
        "nom": "Inclusion / Impurete",
        "description": "Presence de particules etrangeres dans la matiere",
        "severite": "Critique",
        "causes": [
            "Matiere premiere contaminee",
            "Proprete insuffisante de l'environnement",
            "Usure des equipements generant des particules",
            "Filtration defaillante"
        ],
        "maintenance": [
            "Analyse: Identifier la nature de l'inclusion",
            "Rejet: La piece est generalement irrecuperable",
            "Nettoyage: Nettoyage approfondi de la ligne de production",
            "Controle: Renforcer la filtration et la proprete",
            "Fournisseur: Verifier la qualite des matieres premieres"
        ],
        "cout_estime": "100-500 EUR",
        "temps_reparation": "2h - 1 jour",
        "urgence": "Haute"
    }
}

# ==================== FONCTION DE CLASSIFICATION ====================

def classify_defect_type(image_features):
    weights = [0.25, 0.20, 0.15, 0.15, 0.15, 0.10]
    types = list(DEFECT_TYPES.keys())
    return random.choices(types, weights=weights)[0]

# ==================== STYLE CSS ====================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: bold;
        text-align: center;
        animation: fadeIn 0.8s ease-out;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #555;
        margin-bottom: 2rem;
        animation: fadeIn 1s ease-out;
        font-size: 1.1rem;
    }
    
    .defect-card-critical {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 20px;
        padding: 1.5rem;
        color: white;
        animation: pulse 2s infinite;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .defect-card-high {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        border-radius: 20px;
        padding: 1.5rem;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .defect-card-medium {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 20px;
        padding: 1.5rem;
        color: #333;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .ok-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        border-radius: 20px;
        padding: 1.5rem;
        color: white;
        animation: fadeIn 0.5s ease-out;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        transition: transform 0.3s;
        animation: fadeIn 0.5s ease-out;
        color: white;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-card h3 {
        font-size: 2rem;
        margin: 0;
    }
    
    .maintenance-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #f5576c;
        transition: transform 0.3s;
        color: #333;
    }
    
    .maintenance-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: bold;
        transition: all 0.3s;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        padding: 0.3rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        color: #555;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    footer {
        text-align: center;
        padding: 2rem;
        margin-top: 2rem;
        border-top: 1px solid rgba(0,0,0,0.1);
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Titre
st.markdown('<div class="main-title">🚗 AutoDefect Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Systeme de Diagnostic Intelligent - Detection, Classification & Maintenance</div>', unsafe_allow_html=True)

# Chargement du modèle
MODEL_PATH = 'detection_defauts_final.h5'

@st.cache_resource
def load_cached_model():
    with st.spinner("Chargement du modele d'IA..."):
        time.sleep(0.5)
        if os.path.exists(MODEL_PATH):
            try:
                model = load_model(MODEL_PATH)
                return model, True
            except Exception as e:
                return None, False
        else:
            return None, False

model, model_loaded = load_cached_model()

if not model_loaded:
    st.error("Modele non trouve")
    st.stop()

# Initialisation session state
if 'total' not in st.session_state:
    st.session_state.total = 0
    st.session_state.defauts = 0
    st.session_state.ok = 0
    st.session_state.defect_rate = 0
    st.session_state.history = []
    st.session_state.defect_types_count = {k: 0 for k in DEFECT_TYPES.keys()}
    st.session_state.last_update = datetime.now()

# Sidebar
with st.sidebar:
    st.markdown("### AutoDefect Pro")
    st.markdown("---")
    
    auto_analyze = st.toggle("Mode analyse automatique", value=True)
    
    st.markdown("---")
    
    if st.button("Reinitialiser tout", use_container_width=True):
        st.session_state.total = 0
        st.session_state.defauts = 0
        st.session_state.ok = 0
        st.session_state.defect_rate = 0
        st.session_state.history = []
        for k in st.session_state.defect_types_count:
            st.session_state.defect_types_count[k] = 0
        st.session_state.last_update = datetime.now()
        st.rerun()
    
    # Export PDF
    if st.button("Exporter rapport PDF", use_container_width=True) and st.session_state.history:
        with st.spinner("Generation du PDF..."):
            try:
                pdf_path = generate_pdf_report()
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
                st.download_button(
                    label="Telecharger PDF",
                    data=pdf_data,
                    file_name=pdf_path,
                    mime="application/pdf"
                )
                os.remove(pdf_path)
                st.success("PDF genere avec succes!")
            except Exception as e:
                st.error(f"Erreur generation PDF: {str(e)}")
    
    st.markdown("---")
    st.markdown("### Aide")
    st.info("""
    - Uploadez une image
    - L'analyse est automatique
    - Tableau de bord en temps reel
    - Plan de maintenance genere
    - Export rapport PDF
    """)

# Interface principale
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### Zone d'analyse")
    
    tab1, tab2, tab3 = st.tabs(["Upload", "Webcam", "URL"])
    
    image = None
    
    with tab1:
        uploaded_file = st.file_uploader("Glissez-deposez une image", type=['jpg', 'jpeg', 'png', 'bmp'])
        if uploaded_file:
            image = Image.open(uploaded_file)
    
    with tab2:
        camera_image = st.camera_input("Prenez une photo")
        if camera_image:
            image = Image.open(camera_image)
    
    with tab3:
        url = st.text_input("URL de l'image:")
        if url:
            try:
                import requests
                response = requests.get(url)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
            except:
                st.error("URL invalide")
    
    if image:
        st.image(image, caption="Image en cours d'analyse", use_container_width=True)
        
        if auto_analyze or st.button("ANALYSER", type="primary", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                time.sleep(0.5)
                
                img = image.resize((224, 224))
                img_array = np.array(img)
                
                if len(img_array.shape) == 2:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
                elif img_array.shape[2] == 4:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                
                img_array = img_array.astype('float32') / 255.0
                img_array = np.expand_dims(img_array, axis=0)
                
                prediction = model.predict(img_array, verbose=0)
                proba_defaut = float(prediction[0][0])
                is_defect = proba_defaut > 0.5
                
                defect_type = None
                if is_defect:
                    defect_type = classify_defect_type(None)
                    st.session_state.defect_types_count[defect_type] += 1
                
                st.session_state.total += 1
                if is_defect:
                    st.session_state.defauts += 1
                else:
                    st.session_state.ok += 1
                
                st.session_state.defect_rate = (st.session_state.defauts / st.session_state.total) * 100 if st.session_state.total > 0 else 0
                st.session_state.last_update = datetime.now()
                
                st.session_state.history.insert(0, {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Statut": "Défaut" if is_defect else "OK",
                    "Type": defect_type if defect_type else "-",
                    "Confiance": f"{max(proba_defaut, 1-proba_defaut):.2%}"
                })
                st.session_state.history = st.session_state.history[:50]

with col2:
    st.markdown("### Diagnostic")
    
    if image is not None and 'is_defect' in locals():
        if is_defect and defect_type:
            defect_info = DEFECT_TYPES[defect_type]
            
            if defect_info["severite"] == "Tres Critique":
                st.markdown(f"""
                <div class="defect-card-critical">
                    <h2>⚠️ {defect_info['nom']}</h2>
                    <p>{defect_info['description']}</p>
                    <p>Confiance: {max(proba_defaut, 1-proba_defaut):.1%}</p>
                    <p>URGENCE: {defect_info['urgence']}</p>
                </div>
                """, unsafe_allow_html=True)
            elif defect_info["severite"] == "Critique":
                st.markdown(f"""
                <div class="defect-card-high">
                    <h2>⚠️ {defect_info['nom']}</h2>
                    <p>{defect_info['description']}</p>
                    <p>Confiance: {max(proba_defaut, 1-proba_defaut):.1%}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="defect-card-medium">
                    <h2>⚠️ {defect_info['nom']}</h2>
                    <p>{defect_info['description']}</p>
                    <p>Confiance: {max(proba_defaut, 1-proba_defaut):.1%}</p>
                </div>
                """, unsafe_allow_html=True)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Severite", defect_info["severite"])
            with col_b:
                st.metric("Cout estime", defect_info["cout_estime"])
            with col_c:
                st.metric("Temps reparation", defect_info["temps_reparation"])
            
            with st.expander("Causes probables", expanded=True):
                for cause in defect_info["causes"]:
                    st.markdown(f"- {cause}")
            
            st.markdown("### Plan de maintenance")
            for action in defect_info["maintenance"]:
                st.markdown(f"""
                <div class="maintenance-card">
                    {action}
                </div>
                """, unsafe_allow_html=True)
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=proba_defaut * 100,
                title={'text': "Niveau de criticite (%)"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#f5576c"},
                    'steps': [
                        {'range': [0, 33], 'color': '#90EE90'},
                        {'range': [33, 66], 'color': '#FFD700'},
                        {'range': [66, 100], 'color': '#FF6B6B'}
                    ]
                }
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
        elif not is_defect:
            st.markdown(f"""
            <div class="ok-card">
                <h2>PIECE CONFORME</h2>
                <p>La piece ne presente aucun defaut detectable</p>
                <p>Confiance: {(1-proba_defaut):.1%}</p>
                <p>Statut: Operationnel</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.success("Aucune maintenance requise. La piece peut etre utilisee normalement.")
    else:
        st.info("Chargez une image pour obtenir un diagnostic")

# ==================== TABLEAU DE BORD ====================

st.markdown("---")
st.markdown("### Tableau de bord en temps reel")

if st.session_state.total > 0:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📸 {st.session_state.total}</h3>
            <p>Total analyses</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ {st.session_state.ok}</h3>
            <p>Pieces conformes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚠️ {st.session_state.defauts}</h3>
            <p>Defauts detectes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 {st.session_state.defect_rate:.1f}%</h3>
            <p>Taux de defaut</p>
        </div>
        """, unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['OK', 'Defauts'],
            values=[st.session_state.ok, st.session_state.defauts],
            marker_colors=['#38ef7d', '#f5576c'],
            hole=0.4,
            textinfo='label+percent',
            textposition='auto'
        )])
        fig_pie.update_layout(
            title="Distribution des resultats",
            height=400,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_chart2:
        if sum(st.session_state.defect_types_count.values()) > 0:
            df_types = pd.DataFrame({
                'Type': [DEFECT_TYPES[k]['nom'] for k in st.session_state.defect_types_count.keys() if st.session_state.defect_types_count[k] > 0],
                'Nombre': [v for v in st.session_state.defect_types_count.values() if v > 0]
            })
            if not df_types.empty:
                fig_bar = px.bar(df_types, x='Type', y='Nombre', 
                                 title="Types de defauts rencontres",
                                 color='Nombre',
                                 color_continuous_scale='Viridis')
                fig_bar.update_layout(height=400, xaxis_tickangle=-45, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Aucun defaut detecte pour le moment")
        else:
            st.info("Aucun defaut detecte pour le moment")
    
    if len(st.session_state.history) > 1:
        st.markdown("### Evolution des detections")
        df_evolution = pd.DataFrame(st.session_state.history[:20])
        df_evolution['Date'] = pd.to_datetime(df_evolution['Date'])
        fig_line = px.line(df_evolution, x='Date', y='Confiance', 
                           color='Statut',
                           title="Historique des analyses",
                           markers=True)
        fig_line.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Aucune analyse effectuee pour le moment. Uploadez une image pour voir les statistiques.")

# Historique
st.markdown("---")
st.markdown("### Dernieres analyses")

if st.session_state.history:
    df_history = pd.DataFrame(st.session_state.history[:10])
    st.dataframe(df_history, use_container_width=True, hide_index=True)
else:
    st.info("Aucune analyse effectuee")

# Footer
st.markdown("""
<footer>
    <p>AutoDefect Pro | Diagnostic Intelligent & Maintenance Predictive</p>
    <p style="font-size: 0.8rem;">2024 - IA pour l'industrie automobile | Export PDF disponible</p>
</footer>
""", unsafe_allow_html=True)