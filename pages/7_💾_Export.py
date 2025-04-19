import streamlit as st
import pandas as pd
import sqlite3

st.title("💾 Export & téléchargement")

conn = sqlite3.connect('stations_velo.db')
velos = pd.read_sql_query('SELECT * FROM velos', conn)
stations = pd.read_sql_query('SELECT * FROM stations', conn)

st.header("Exporter les données filtrées")
station_names = ['Toutes'] + sorted(stations['Nom'].unique())
selected_station = st.selectbox('Station à exporter', station_names)
if selected_station != 'Toutes':
    station_id = stations[stations['Nom'] == selected_station]['ID'].iloc[0]
    df = velos[velos['STATION_ID'] == station_id]
else:
    df = velos.copy()
st.dataframe(df.head(100))
st.download_button("Télécharger CSV", df.to_csv(index=False).encode('utf-8'), file_name="velos_export.csv", mime="text/csv")

st.header("Exporter un graphique (PNG)")
st.write("Pour exporter un graphique, faites un clic droit dessus puis 'Enregistrer sous...'.")
