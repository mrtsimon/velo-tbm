import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import sqlite3

st.set_page_config(page_title="Carte des stations de vélos TBM", layout="wide", initial_sidebar_state="expanded")

# Titre de l'application
st.title("Carte des stations de vélos TBM")

@st.cache_data
def load_data():
    conn = sqlite3.connect('/home/simon/velo-tbm/stations_velo.db')
    
    stations = pd.read_sql_query("SELECT * FROM stations", conn)
    
    velos = pd.read_sql_query("SELECT * FROM velos", conn)
    
    # Récupérer les données les plus récentes pour chaque station
    latest_velos = velos.sort_values('date', ascending=False).drop_duplicates(subset=['STATION_ID'])
    
    # Fusionner les tables stations et velos
    merged_data = pd.merge(
        stations,
        latest_velos,
        left_on='ID',  # Ajustez ces colonnes selon vos noms réels
        right_on='STATION_ID',
        how='left'  # Pour garder toutes les stations, même sans données vélos
    )
        
    conn.close()
    
    return merged_data

try:
    merged_data = load_data()

    # Création de deux colonnes pour la liste et la carte
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Liste des stations")
        # Création d'une liste déroulante avec les noms des stations
        selected_station = st.selectbox(
            "Sélectionnez une station",
            options=merged_data['Nom'].unique(),
            index=None,
            placeholder="Choisissez une station..."
        )

    with col2:
        st.subheader("Carte des stations")
        
        # Création de la carte (centrée sur Bordeaux)
        m = folium.Map(location=[44.837789, -0.57918], zoom_start=13)
        
        # Ajout des marqueurs pour chaque station
        # Vérifiez si les colonnes pos_y et pos_x existent
        if 'pos_y' in merged_data.columns and 'pos_x' in merged_data.columns:
            for idx, row in merged_data.iterrows():
                # Vérifiez si les valeurs ne sont pas nulles
                if pd.notna(row['pos_y']) and pd.notna(row['pos_x']):
                    # Préparez le texte du popup avec les infos vélos si disponible
                    popup_text = f"<b>{row.get('Nom', 'Station')}</b><br>"
                    
                    # Vérifier si des données vélos sont disponibles
                    has_velo_data = pd.notna(row.get('date'))
                    
                    if has_velo_data:
                        tooltip_text = f"""<b>{row.get('Nom', 'Station')}</b><br>
                            Vélos classiques: {row.get('nb_classiq', 'N/A')}<br>
                            Vélos électriques: {row.get('nb_elec', 'N/A')}<br>
                            Total vélos: {row.get('nb_total', 'N/A')}<br>
                            Places disponibles: {row.get('nb_places', 'N/A')}<br>
                            Capacité totale: {row.get('capacite', 'N/A')}<br>
                            État: {row.get('etat', 'N/A')}<br>
                            Dernière mise à jour: {row.get('date', 'N/A')}
                            """
                    else:
                        # Texte par défaut si aucune donnée n'est disponible
                        tooltip_text = f"{row.get('Nom', 'Station')}<br>Aucune donnée disponible"
                    
                    folium.Marker(
                        [float(row['pos_y']), float(row['pos_x'])],
                        popup=folium.Popup(popup_text, max_width=400),
                        tooltip=tooltip_text
                    ).add_to(m)
        
        # Affichage de la carte
        folium_static(m)

except Exception as e:
    st.error(f"Une erreur s'est produite : {str(e)}")
