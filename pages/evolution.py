import sqlite3
import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import openai
import io
import chat_db_utils
import pydeck as pdk

# Charger la clé API OpenAI si présente
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

st.set_page_config(page_title="Évolution du taux d'occupation des stations de vélos TBM", layout="wide", initial_sidebar_state="collapsed")

# Titre principal
st.markdown("<h1 style='text-align:center;'>Évolution du taux d'occupation des stations de vélos TBM</h1>", unsafe_allow_html=True)

# Charger un échantillon des données vélos (1 ligne sur 10)
conn = sqlite3.connect('/home/simon/velo-tbm/stations_velo.db')
velos = pd.read_sql_query("SELECT * FROM velos WHERE ID % 10 = 0", conn)
conn.close()

# Charger toutes les données météo (plus léger)
conn = sqlite3.connect('/home/simon/velo-tbm/meteo.db')
meteo = pd.read_sql_query("SELECT * FROM meteo", conn)
conn.close()

# Conversion robuste pour les dates ISO 8601 avec timezone
velos['date'] = pd.to_datetime(velos['date'], errors='coerce', utc=True)
velos['date'] = velos['date'].dt.tz_convert(None)
meteo['dh_utc'] = pd.to_datetime(meteo['dh_utc'], errors='coerce')

# Drop les lignes où la date est NaT
velos = velos.dropna(subset=['date'])
meteo = meteo.dropna(subset=['dh_utc'])

# Fusionner les deux tables sur la date la plus proche (tolérance de 30 min)
merged = pd.merge_asof(
    velos.sort_values('date'),
    meteo.sort_values('dh_utc'),
    left_on='date',
    right_on='dh_utc',
    direction='backward',
    tolerance=pd.Timedelta('30min')
)

# Calculer la capacité si elle n'existe pas
if 'capacite' not in merged or merged['capacite'].isnull().any():
    merged['capacite'] = merged['nb_total'].fillna(0) + merged['nb_places'].fillna(0)

# Calculer le taux d'occupation
merged['taux_occupation'] = merged['nb_total'] / merged['capacite']

# Charger les stations pour le filtre
stations_lookup = pd.read_sql_query("SELECT ID, Nom FROM stations ORDER BY Nom;", sqlite3.connect('/home/simon/velo-tbm/stations_velo.db'))
station_options = dict(zip(stations_lookup['Nom'], stations_lookup['ID']))

# --- FILTRES ALIGNÉS ---
filters = st.columns([1,1,1,2,2,2])
with filters[0]:
    start_date = st.date_input('Date de début', datetime.date.today() - timedelta(days=7), key='start_date')
    start_time = st.time_input('Heure de début', value=datetime.time(0, 0), key='start_time')
with filters[1]:
    end_date = st.date_input('Date de fin', datetime.date.today(), key='end_date')
    end_time = st.time_input('Heure de fin', value=datetime.time(23, 59), key='end_time')
with filters[2]:
    group_by_date = st.selectbox('Grouper par', ['heure', 'jour', 'semaine', 'mois'], key='group_by')
with filters[3]:
    # Filtre station vélo (par nom)
    station_names = ['Toutes'] + sorted(station_options.keys())
    selected_station = st.selectbox('Station vélo', options=station_names, key='station')
with filters[4]:
    # Filtre type de vélo
    velo_type = st.selectbox('Type de vélo', options=['Tous', 'Classique', 'Electrique'], key='velo_type')
with filters[5]:
    # Sélecteur KPI dynamique (toutes colonnes numériques météo + taux d'occupation)
    meteo_num_cols = [col for col in meteo.columns if str(meteo[col].dtype) in ['float64', 'int64'] and col not in ['id_station']]
    kpi_options = ["Taux d'occupation moyen"] + meteo_num_cols
    selected_kpis = st.multiselect('KPI à afficher', kpi_options, default=["Taux d'occupation moyen", 'temperature', 'pluie_1h'])

# Correction conversion pour le filtrage
start_datetime = pd.to_datetime(str(start_date) + ' ' + str(start_time))
end_datetime = pd.to_datetime(str(end_date) + ' ' + str(end_time))

# Filtre station vélo
if selected_station != 'Toutes':
    merged = merged[merged['STATION_ID'] == station_options[selected_station]]

# Filtre type de vélo
if velo_type == 'Classique':
    merged['nb_total'] = merged['nb_classiq']
elif velo_type == 'Electrique':
    merged['nb_total'] = merged['nb_elec']

# Filtre date
mask = (merged['date'] >= start_datetime) & (merged['date'] <= end_datetime)
filtered = merged.loc[mask].copy()

# Grouper les données par date
if group_by_date == 'heure':
    filtered['date_group'] = filtered['date'].dt.floor('h')
elif group_by_date == 'jour':
    filtered['date_group'] = filtered['date'].dt.date
elif group_by_date == 'semaine':
    filtered['date_group'] = filtered['date'].dt.to_period('W').astype(str)
elif group_by_date == 'mois':
    filtered['date_group'] = filtered['date'].dt.to_period('M').astype(str)

# --- KPIs dynamiques ---
# Calcul du taux d'occupation moyen global (moyenne des moyennes stations)
occupation_station = filtered.groupby(['date_group', 'STATION_ID'])['taux_occupation'].mean().reset_index()
occupation_globale = occupation_station.groupby('date_group')['taux_occupation'].mean() * 100  # en %

plot_df = pd.DataFrame({'date_group': occupation_globale.index})
if "Taux d'occupation moyen" in selected_kpis:
    plot_df["Taux d'occupation moyen"] = occupation_globale.values
for col in meteo_num_cols:
    if col in selected_kpis:
        plot_df[col] = filtered.groupby('date_group')[col].mean().values

# --- TABLEAU SYNTHÈSE ---
def get_emoji_meteo_series(df_grouped, meteo_df):
    meteo_grouped = meteo_df.copy()
    if 'date_group' not in meteo_grouped:
        if group_by_date == 'heure':
            meteo_grouped['date_group'] = meteo_grouped['dh_utc'].dt.floor('h')
        elif group_by_date == 'jour':
            meteo_grouped['date_group'] = meteo_grouped['dh_utc'].dt.date
        elif group_by_date == 'semaine':
            meteo_grouped['date_group'] = meteo_grouped['dh_utc'].dt.to_period('W').astype(str)
        elif group_by_date == 'mois':
            meteo_grouped['date_group'] = meteo_grouped['dh_utc'].dt.to_period('M').astype(str)
    meteo_mode = meteo_grouped.groupby('date_group')['temps_omm'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)
    omm_to_emoji = {
        '61': '🌧️',  # Pluie faible
        '63': '🌦️',  # Pluie modérée
        # Ajoute d'autres codes si besoin
    }
    emojis = [omm_to_emoji.get(str(meteo_mode.get(d)), '❓') for d in df_grouped['date_group']]
    return pd.Series(emojis, index=df_grouped['date_group'])

emoji_series = get_emoji_meteo_series(plot_df, meteo)
table_df = plot_df.copy()
table_df['Météo'] = emoji_series.values
pression_moyenne = filtered.groupby('date_group')['pression'].mean().reindex(table_df['date_group'])
table_df['Couverture (pression)'] = pression_moyenne.apply(lambda x: '☀️' if x > 1020 else '☁️' if x < 1010 else '⛅')

# Réorganiser les colonnes pour que les KPI sélectionnés apparaissent dans l'ordre choisi
cols = ['date_group', 'Météo', 'Couverture (pression)'] + selected_kpis
cols = [c for c in cols if c in table_df.columns]
table_df = table_df[cols]

# --- LAYOUT GRAPHIQUE + CHAT ---
graph_col, chat_col = st.columns([2,1])
with graph_col:
    fig = go.Figure()
    if "Taux d'occupation moyen" in plot_df:
        fig.add_trace(go.Scatter(x=plot_df['date_group'], y=plot_df["Taux d'occupation moyen"],
                                mode='lines+markers', name="Taux d'occupation moyen (%)", yaxis='y1'))
    for col in meteo_num_cols:
        if col in selected_kpis:
            fig.add_trace(go.Scatter(x=plot_df['date_group'], y=plot_df[col], mode='lines+markers', name=col))
    fig.update_layout(
        title="Évolution des KPIs",
        xaxis_title='Date',
        yaxis=dict(title="Taux d'occupation moyen (%)", color='blue'),
        legend=dict(x=0.01, y=0.99, bordercolor="Black", borderwidth=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.write('### Synthèse par période')
    st.dataframe(table_df, hide_index=True)

# --- FLUX DE VÉLOS ENTRE STATIONS ---
st.write('## Flux de vélos entre stations')

# Charger les infos stations (ID, Nom, pos_x, pos_y)
stations_df = pd.read_sql_query('SELECT * FROM stations', sqlite3.connect('stations_velo.db'))

# Filtrer les données vélos sur la plage de dates sélectionnée
df_flux = velos[(velos['date'] >= start_datetime) & (velos['date'] <= end_datetime)]

# Pour chaque station, calculer la variation de stock (dernier - premier)
def get_variation(df):
    d1 = df.sort_values('date').iloc[0]['nb_total']
    d2 = df.sort_values('date').iloc[-1]['nb_total']
    return d2 - d1

var_par_station = (
    df_flux.groupby('STATION_ID').apply(get_variation)
    .reset_index(name='variation')
)

# Joindre avec noms et positions
top_flux = var_par_station.merge(stations_df, left_on='STATION_ID', right_on='ID')

# Top arrivées (plus grosse hausse)
top_arrivees = top_flux.sort_values('variation', ascending=False).head(5)[['Nom', 'variation']]
# Top départs (plus grosse baisse)
top_depart = top_flux.sort_values('variation').head(5)[['Nom', 'variation']]

col1, col2 = st.columns(2)
with col1:
    st.markdown('### Stations ayant reçu le plus de vélos')
    st.dataframe(top_arrivees, hide_index=True)
with col2:
    st.markdown('### Stations ayant perdu le plus de vélos')
    st.dataframe(top_depart, hide_index=True)

# Carte heatmap des variations nettes par station
st.markdown('### Carte des variations nettes par station (heatmap)')
if not top_flux.empty:
    # Ajoute une colonne couleur selon la variation (rouge = perte, vert = gain)
    def color_fn(var):
        if var > 0:
            return [0, 180, 0, 180]  # Vert
        elif var < 0:
            return [220, 0, 0, 180]  # Rouge
        else:
            return [180, 180, 180, 120]  # Gris

    top_flux['color'] = top_flux['variation'].apply(color_fn)
    top_flux['absvar'] = top_flux['variation'].abs()

    layer_points = pdk.Layer(
        'ScatterplotLayer',
        data=top_flux,
        get_position='[pos_x, pos_y]',
        get_color='color',
        get_radius='absvar * 10 + 100',
        pickable=True,
        auto_highlight=True,
    )

    midpoint = [top_flux['pos_y'].mean(), top_flux['pos_x'].mean()]
    st.pydeck_chart(pdk.Deck(
        layers=[layer_points],
        initial_view_state=pdk.ViewState(
            latitude=midpoint[0], longitude=midpoint[1], zoom=13, pitch=0
        ),
        map_style='mapbox://styles/mapbox/light-v9'
    ))
else:
    st.info("Pas assez de données pour afficher la heatmap.")

# --- Gestion historique des conversations IA ---
chat_db_utils.init_db()

if 'current_conversation_id' not in st.session_state:
    # Si aucune conversation, en créer une
    conversations = chat_db_utils.list_conversations()
    if conversations:
        st.session_state['current_conversation_id'] = conversations[0]['id']
    else:
        st.session_state['current_conversation_id'] = chat_db_utils.create_conversation()

with chat_col:
    st.subheader("Assistant IA")
    # Gestion affichage historique (toggle)
    if 'show_history' not in st.session_state:
        st.session_state['show_history'] = True
    col_btn, col_new = st.columns([1,1])
    with col_btn:
        if st.button("📚 Historique", use_container_width=True):
            st.session_state['show_history'] = not st.session_state['show_history']
    with col_new:
        if st.button("📝 Nouvelle conversation", use_container_width=True):
            import chat_db_utils
            st.session_state['current_conversation_id'] = chat_db_utils.create_conversation()
            st.rerun()
    # Affichage de l'historique des conversations
    import chat_db_utils
    conversations = chat_db_utils.list_conversations()
    conv_titles = [f"{c['title']} ({c['updated_at'][:16].replace('T',' ')})" for c in conversations]
    conv_ids = [c['id'] for c in conversations]
    if st.session_state['show_history']:
        if conv_titles:
            selected_idx = st.radio("Conversations", conv_titles, index=conv_ids.index(st.session_state['current_conversation_id']) if st.session_state['current_conversation_id'] in conv_ids else 0)
            st.session_state['current_conversation_id'] = conv_ids[conv_titles.index(selected_idx)]
    # --- Chat interactif façon ChatGPT avec zone scrollable ---
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    # Charger l'historique de la conversation sélectionnée
    db_msgs = chat_db_utils.get_messages(st.session_state['current_conversation_id'])
    st.session_state['messages'] = [
        {'role': m['role'], 'content': m['content']} for m in db_msgs
    ]
    # Affichage des messages dans une zone scrollable
    scrollable_height = 400
    chat_scroll_id = "chat-scrollable-container"
    st.markdown(
        f'''<div id="{chat_scroll_id}" style="height: {scrollable_height}px; overflow-y: auto; border: 1px solid #eee; border-radius: 10px; padding: 8px; background: #fafbfc; display: flex; flex-direction: column-reverse;">''',
        unsafe_allow_html=True
    )
    # Affiche les messages du plus récent au plus ancien pour que le scroll soit en bas
    for message in reversed(st.session_state['messages']):
        with st.chat_message(message['role'], avatar=("👤" if message['role']=="user" else "🚲")):
            st.markdown(message['content'])
    st.markdown("</div>", unsafe_allow_html=True)
    # Barre d'entrée du chat (toujours en bas)
    if prompt := st.chat_input("Posez une question sur les données affichées..."):
        st.session_state['messages'].append({"role": "user", "content": prompt})
        chat_db_utils.add_message(st.session_state['current_conversation_id'], 'user', prompt)
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🚲"):
            # Ajoute un contexte sur les données filtrées
            chat_df = pd.DataFrame({'date_group': plot_df['date_group']})
            for col in selected_kpis:
                if col == "Taux d'occupation moyen" and "Taux d'occupation moyen" in plot_df:
                    chat_df[col] = plot_df["Taux d'occupation moyen"]
                elif col in plot_df:
                    chat_df[col] = plot_df[col]
            chat_df = chat_df.head(100)
            csv_sample = chat_df.to_csv(index=False)
            system_prompt = (
                "Tu es un assistant d'analyse de données vélo. "
                "Tu reçois la question de l'utilisateur et un extrait CSV des données filtrées. "
                "Sois particulièrement vigilant sur la complétude des données : vérifie s'il y a des dates ou périodes où certaines valeurs sont manquantes ou absentes, "
                "et indique-le à l'utilisateur si c'est le cas, pour éviter toute interprétation erronée. "
                "Donne une réponse concise et pédagogique, tu peux établir des corrélations, tendances ou statistiques."
            )
            messages_api = [
                {"role": "system", "content": system_prompt},
                *st.session_state['messages'][:-1],
                {"role": "user", "content": f"Question: {prompt}\n\nDonnées filtrées (CSV):\n{csv_sample}"}
            ]
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages_api,
                stream=True,
                max_tokens=400,
                temperature=0.2
            )
            response = st.write_stream(stream)
        st.session_state['messages'].append({"role": "assistant", "content": response})
        chat_db_utils.add_message(st.session_state['current_conversation_id'], 'assistant', response)
# Optionnel : afficher les données intermédiaires
toggle = st.expander("Afficher les données intermédiaires")
with toggle:
    st.write(filtered.head())
    st.write(occupation_station.head())
    st.write(occupation_globale.head())
    st.write(plot_df.head())
    st.write(table_df.head())
