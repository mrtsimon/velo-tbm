import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3

st.title("🕒 Heatmaps temporelles")

conn = sqlite3.connect('stations_velo.db')
velos = pd.read_sql_query('SELECT * FROM velos', conn)
stations = pd.read_sql_query('SELECT * FROM stations', conn)

station_names = ['Toutes'] + sorted(stations['Nom'].unique())
selected_station = st.selectbox('Station', station_names)
if selected_station != 'Toutes':
    station_id = stations[stations['Nom'] == selected_station]['ID'].iloc[0]
    df = velos[velos['STATION_ID'] == station_id]
else:
    df = velos.copy()

# Conversion stricte de la colonne date (encore plus robuste)
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df[df['date'].notnull()].copy()
df['jour'] = df['date'].dt.day_name()
df['heure'] = df['date'].dt.hour
heatmap_data = df.groupby(['jour', 'heure'])['nb_total'].mean().reset_index()
heatmap_pivot = heatmap_data.pivot(index='heure', columns='jour', values='nb_total')
heatmap_pivot = heatmap_pivot.reindex(columns=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

fig = px.imshow(
    heatmap_pivot,
    labels=dict(x="Jour", y="Heure", color="Nb vélos moyen"),
    aspect="auto"
)
st.plotly_chart(fig, use_container_width=True)
