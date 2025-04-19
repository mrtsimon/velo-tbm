import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import sqlite3

# Configuration de la page
st.set_page_config(page_title="Stations de Vélos TBM", layout="wide", initial_sidebar_state="expanded")


# Titre de l'application
st.title("Stations de Vélos TBM")

# Chargement des données depuis SQLite
@st.cache_data
def load_data():
    conn = sqlite3.connect('/home/simon/velo-tbm/stations_velo.db')
    
    # Chargement de la table stations
    stations = pd.read_sql_query("SELECT * FROM stations", conn)
    
    # Chargement de la table vélo
    velos = pd.read_sql_query("SELECT * FROM velos", conn)
    
    merged_data = pd.merge(stations, velos, on='station_id', how='left')
    
    conn.close()
    
    return stations, velos, merged_data

try:
    # Chargement des données
    stations, velos, merged_data = load_data()
    
    # Affichons d'abord les premières lignes pour inspection
    st.subheader("Aperçu des données")
    tabs = st.tabs(["Stations", "Vélos"])
    
    with tabs[0]:
        st.write("Table Stations:")
        st.dataframe(stations.head())
        st.text(f"Colonnes disponibles: {', '.join(stations.columns)}")
    
    with tabs[1]:
        st.write("Table Vélos:")
        st.dataframe(velos.head())
        st.text(f"Colonnes disponibles: {', '.join(velos.columns)}")
    
    # Création de deux colonnes pour la carte et les données
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Carte des stations")
        
        # Création de la carte (centrée sur Bordeaux)
        m = folium.Map(location=[44.837789, -0.57918], zoom_start=13)
        
        # Ajout des marqueurs pour chaque station
        # Vérifiez si les colonnes pos_y et pos_x existent
        if 'pos_y' in stations.columns and 'pos_x' in stations.columns:
            for idx, row in stations.iterrows():
                # Vérifiez si les valeurs ne sont pas nulles
                if pd.notna(row['pos_y']) and pd.notna(row['pos_x']):
                    # Préparez le texte du popup avec les infos vélos si disponible
                    station_id = row.get('id', row.get('station_id', None))
                    popup_text = f"<b>{row.get('nom', 'Station')}</b><br>"
                    tooltip_text = row.get('nom', 'Station')  # Valeur par défaut du tooltip
                    
                    if station_id is not None and 'station_id' in velos.columns:
                        # Récupérer la dernière mise à jour pour cette station
                        station_velos = velos[velos['station_id'] == station_id].sort_values('date', ascending=False)
                        if not station_velos.empty:
                            latest_data = station_velos.iloc[0]
                            popup_text += f"""
                            Vélos classiques: {latest_data.get('nb_classiq', 'N/A')}<br>
                            Vélos électriques: {latest_data.get('nb_elec', 'N/A')}<br>
                            Total vélos: {latest_data.get('nb_total', 'N/A')}<br>
                            Places disponibles: {latest_data.get('nb_places', 'N/A')}<br>
                            Capacité totale: {latest_data.get('capacite', 'N/A')}<br>
                            État: {latest_data.get('etat', 'N/A')}<br>
                            Dernière mise à jour: {latest_data.get('date', 'N/A')}
                            """
                            # Mise à jour du tooltip avec les données récentes
                            tooltip_text = f"Station: {row.get('nom', 'Station')} | Vélos: {latest_data.get('nb_total', 'N/A')}/{latest_data.get('capacite', 'N/A')} | Électriques: {latest_data.get('nb_elec', 'N/A')}"
                    
                    folium.Marker(
                        [float(row['pos_y']), float(row['pos_x'])],
                        popup=folium.Popup(popup_text, max_width=300),
                        tooltip=tooltip_text
                    ).add_to(m)
        
        # Affichage de la carte
        folium_static(m)

    with col2:
        st.subheader("Liste des stations et disponibilité")
        
        # Joindre les données de stations et vélos si nécessaire
        if 'id' in stations.columns and 'station_id' in velos.columns:
            merged_data = pd.merge(
                stations, 
                velos, 
                left_on='id', 
                right_on='station_id', 
                how='left'
            )
            st.dataframe(merged_data)
        else:
            st.dataframe(stations)

except Exception as e:
    st.error(f"Une erreur s'est produite : {str(e)}")
    
    # Affichons la structure de la base de données pour le débogage
    try:
        conn = sqlite3.connect('/home/simon/velo-tbm/stations_velo.db')
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
        st.write("Tables disponibles dans la base de données :")
        st.write(tables)
        
        # Affichons également la structure des tables
        for table_name in tables['name']:
            st.write(f"Structure de la table '{table_name}' :")
            table_info = pd.read_sql_query(f"PRAGMA table_info({table_name});", conn)
            st.write(table_info)
            
            # Affichons les 5 premières lignes
            sample_data = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5;", conn)
            st.write(f"Échantillon de données de '{table_name}' :")
            st.write(sample_data)
        
        conn.close()
    except Exception as debug_error:
        st.error(f"Erreur lors du débogage : {str(debug_error)}")