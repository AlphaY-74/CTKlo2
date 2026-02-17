import streamlit as st
import json
import os
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
try:
    from streamlit_js_eval import streamlit_js_eval
    HAS_STREAMLIT_JS_EVAL = True
except Exception:
    streamlit_js_eval = None
    HAS_STREAMLIT_JS_EVAL = False

# 1. STYLE & CONFIG
st.set_page_config(page_title="CTKlo SAE Pro", layout="centered")
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .current-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #60a5fa;
        text-align: center; margin-bottom: 20px;
    }
    .stop-row { 
        padding: 10px; 
        border-left: 3px solid #334155; 
        margin-bottom: 5px;
        background-color: #1a1c23;
    }
    .stop-active { border-left: 5px solid #10b981; background-color: #064e3b; font-weight: bold; }
    .stop-passed { border-left: 3px solid #4b5563; color: #6b7280; }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIQUE TECHNIQUE
def check_distance(lat1, lon1, lat2, lon2):
    try:
        R = 6371000 
        dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        return 2 * R * asin(sqrt(a))
    except: return 999999

# 3. BASE DE DONNÉES BUS
BUS_LIBRARY = {
    "102": "Man Lion's Intercity", "110": "Man Lion's City", "210": "Mercedes Intouro",
    "300": "Iveco Crossway LE", "301": "Iveco Crossway Line", "406": "Irizar i6",
    "896": "Irizar i8 Premium", "915": "Setra S 515 LE", "500": "Solaris Urbino"
}

# 4. INITIALISATION DES LIGNES
if 'lignes_config' not in st.session_state:
    if os.path.exists('lignes_config.json'):
        with open('lignes_config.json', 'r') as f:
            st.session_state.lignes_config = json.load(f)
    else:
        st.session_state.lignes_config = {
            "Ligne Test": [
                {"nom": "Départ", "lat": 47.6, "lon": 7.2, "h": "08:00"},
                {"nom": "Centre", "lat": 47.61, "lon": 7.21, "h": "08:15"},
                {"nom": "Terminus", "lat": 47.62, "lon": 7.22, "h": "08:30"}
            ]
        }

if 'idx_arret' not in st.session_state:
    st.session_state.idx_arret = 0

# --- INTERFACE ---
st.title("📟 SAE Intelligent CTKlo")

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Configuration")
    bus_id = st.selectbox("Véhicule", list(BUS_LIBRARY.keys()), format_func=lambda x: f"{x} - {BUS_LIBRARY[x]}")
    
    noms_lignes = list(st.session_state.lignes_config.keys())
    ligne_nom = st.selectbox("Choisir la ligne", noms_lignes)
    
    if st.button("Réinitialiser le trajet"):
        st.session_state.idx_arret = 0
        st.rerun()

# --- COEUR DU SYSTÈME ---
stops = st.session_state.lignes_config.get(ligne_nom, [])

if not stops:
    st.error("Cette ligne ne contient aucun arrêt.")
else:
    # GPS en temps réel
    loc = None
    if HAS_STREAMLIT_JS_EVAL and streamlit_js_eval is not None:
        try:
            loc = streamlit_js_eval(data_key='pos', func_name='getCurrentPosition', delay=3000)
        except Exception:
            loc = None

    if loc and ligne_nom:
        u_lat, u_lon = loc['coords']['latitude'], loc['coords']['longitude']
        st.session_state.idx_arret = len(stops) - 1

    prochain = stops[st.session_state.idx_arret]

    # Calcul distance si GPS actif
    dist_text = "Recherche GPS..."
    if loc:
        u_lat, u_lon = loc['coords']['latitude'], loc['coords']['longitude']
        dist = check_distance(u_lat, u_lon, prochain['lat'], prochain['lon'])
        dist_text = f"{int(dist)} m"
        
        # Passage automatique (50 mètres)
        if dist < 50 and st.session_state.idx_arret < len(stops) - 1:
            st.session_state.idx_arret += 1
            st.toast(f"Arrivée à {prochain['nom']}")
            st.rerun()

    # Affichage Arrêt Actuel
    st.markdown(f"""
        <div class="current-card">
            <p style='margin:0; opacity:0.8;'>PROCHAIN ARRÊT</p>
            <h1 style='margin:0;'>{prochain['nom']}</h1>
            <p style='margin:0; font-size:1.2em;'>Prévu : {prochain['h']} | GPS : {dist_text}</p>
        </div>
        """, unsafe_allow_html=True)

    # --- FEUILLE DE ROUTE CORRIGÉE ---
    st.subheader("📋 Feuille de route")
    for i, s in enumerate(stops):
        if i < st.session_state.idx_arret:
            css_class = "stop-passed"
            status = "✔️"
        elif i == st.session_state.idx_arret:
            css_class = "stop-active"
            status = "➡️"
        else:
            css_class = ""
            status = "⚪"
            
        st.markdown(f"""
            <div class="stop-row {css_class}">
                {status} {s['h']} - {s['nom']}
            </div>
            """, unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    # ... (sélection du bus et de la ligne)
    
    st.divider()
    st.subheader("🆕 Nouvelle Ligne")
    nom_nouvelle_ligne = st.text_input("Nom de la ligne à créer")
    if st.button("Créer la ligne"):
        if nom_nouvelle_ligne and nom_nouvelle_ligne not in st.session_state.lignes_config:
            st.session_state.lignes_config[nom_nouvelle_ligne] = [] # Crée une ligne vide
            # Sauvegarde immédiate dans le fichier JSON
            with open('lignes_config.json', 'w') as f:
                json.dump(st.session_state.lignes_config, f)
            st.success(f"Ligne {nom_nouvelle_ligne} créée !")
            st.rerun()
            
# --- ÉDITEUR ---
with st.expander("🛠️ Modifier les arrêts de cette ligne"):
    st.write("Ajouter un arrêt à la fin :")
    n_n = st.text_input("Nom de l'arrêt")
    c1, c2, c3 = st.columns(3)
    n_lat = c1.number_input("Lat", format="%.6f", value=47.6)
    n_lon = c2.number_input("Lon", format="%.6f", value=7.2)
    n_h = c3.text_input("Heure (HH:MM)")
    
    if st.button("Enregistrer l'arrêt"):
        st.session_state.lignes_config[ligne_nom].append({"nom": n_n, "lat": n_lat, "lon": n_lon, "h": n_h})
        with open('lignes_config.json', 'w') as f:
            json.dump(st.session_state.lignes_config, f)
        st.success("Arrêt ajouté !")
        st.rerun()
