import streamlit as st
import pandas as pd
import pydeck as pdk
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
    
    # Récupérer les données les plus récentes pour chaque station
    latest_velos = velos.sort_values('date', ascending=False).drop_duplicates(subset=['STATION_ID'])
    
    # Fusion des données
    merged_data = pd.merge(stations, latest_velos, left_on='ID', right_on='STATION_ID', how='left')
    
    conn.close()
    
    return stations, latest_velos, merged_data

try:
    # Chargement des données
    stations, latest_velos, merged_data = load_data()
    
    # Création de deux colonnes pour la carte et les données
    col1, col2 = st.columns([2, 2])

    with col1:
        st.subheader("Carte des stations")
        
        # OPTION 1: Utiliser st.map (très simple et rapide)
        # Préparation des données pour st.map
        map_data = merged_data[['pos_y', 'pos_x', 'Nom']].copy()
        map_data.rename(columns={'pos_y': 'lat', 'pos_x': 'lon'}, inplace=True)
        map_data = map_data.dropna(subset=['lat', 'lon'])
        
        # Affichage de la carte simple
        st.map(map_data)
        
        # OPTION 2: Utiliser PyDeck (plus de fonctionnalités, toujours rapide)
        st.subheader("Carte interactive (PyDeck)")
        
        # Préparation des données pour PyDeck
        pydeck_data = merged_data.dropna(subset=['pos_y', 'pos_x']).copy()
        
        # Renommage des colonnes pour PyDeck
        pydeck_data['lat'] = pydeck_data['pos_y'].astype(float)
        pydeck_data['lon'] = pydeck_data['pos_x'].astype(float)
        
        # Déterminer la couleur en fonction de la disponibilité des vélos
        def get_color(row):
            if pd.isna(row.get('nb_total')):
                return [128, 128, 128]  # Gris pour les stations sans données
            
            # Calculer un pourcentage de remplissage
            if pd.notna(row.get('capacite')) and row['capacite'] > 0:
                ratio = row['nb_total'] / row['capacite']
                if ratio > 0.5:
                    return [0, 255, 0]  # Vert pour bonne disponibilité
                elif ratio > 0.2:
                    return [255, 255, 0]  # Jaune pour disponibilité moyenne
                else:
                    return [255, 0, 0]  # Rouge pour faible disponibilité
            return [0, 0, 255]  # Bleu par défaut
        
        pydeck_data['color'] = pydeck_data.apply(get_color, axis=1)
        
        # Créer le layer pour PyDeck
        layer = pdk.Layer(
            "ScatterplotLayer",
            pydeck_data,
            get_position=["lon", "lat"],
            get_radius=100,
            get_fill_color="color",
            pickable=True,
            opacity=0.8,
        )
        
        # Configuration de la vue
        view_state = pdk.ViewState(
            latitude=44.837789,
            longitude=-0.57918,
            zoom=12,
            pitch=0,
        )
        
        # Configuration des tooltips
        tooltip = {
            "html": "<b>{Nom}</b><br>"
                   "Vélos disponibles: {nb_total}<br>"
                   "Places disponibles: {nb_places}<br>"
                   "Dernière mise à jour: {date}",
            "style": {"backgroundColor": "white", "color": "black"}
        }
        
        # Création du deck
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style="mapbox://styles/mapbox/light-v9"
        )
        
        # Affichage de la carte PyDeck
        st.pydeck_chart(deck)

    with col2:
        st.subheader("Liste des stations et disponibilité")
        
        # Utiliser un filtre pour limiter les données affichées
        search = st.text_input("Rechercher une station")
        
        # Filtrer les données
        if search:
            filtered_data = merged_data[merged_data['Nom'].str.contains(search, case=False, na=False)]
        else:
            filtered_data = merged_data
        
        # Limiter le nombre de lignes affichées
        rows_to_display = st.slider("Nombre de stations à afficher", 5, 50, 10)
        
        # Sélectionner les colonnes importantes
        display_columns = ['Nom', 'nb_classiq', 'nb_elec', 'nb_total', 'nb_places', 'capacite', 'etat', 'date']
        display_data = filtered_data[display_columns].head(rows_to_display)
        
        # Afficher un tableau plus léger
        st.dataframe(display_data, use_container_width=True)
        
        # Afficher un graphique pour les stations sélectionnées
        if search:
            st.subheader(f"Évolution des vélos disponibles pour les stations contenant '{search}'")
            
            # Obtenir les IDs des stations filtrées
            station_ids = filtered_data['ID'].unique()
            
            # Charger les données historiques pour ces stations
            conn = sqlite3.connect('/home/simon/velo-tbm/stations_velo.db')
            historical_data = pd.read_sql_query(
                f"SELECT * FROM velos WHERE STATION_ID IN ({','.join(['?'] * len(station_ids))})",
                conn,
                params=station_ids.tolist()
            )
            conn.close()
            
            # Joindre avec les noms des stations
            historical_data = pd.merge(historical_data, stations[['ID', 'Nom']], 
                                       left_on='STATION_ID', right_on='ID', how='left')
            
            # Graphique d'évolution
            st.line_chart(historical_data, x='date', y='nb_total', color='Nom')

except Exception as e:
    st.error(f"Une erreur s'est produite : {str(e)}")