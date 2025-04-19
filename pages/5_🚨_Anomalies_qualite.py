import streamlit as st
import pandas as pd
import sqlite3

st.title("🚨 Anomalies & qualité des données")

conn = sqlite3.connect('stations_velo.db')
velos = pd.read_sql_query('SELECT * FROM velos', conn)
stations = pd.read_sql_query('SELECT * FROM stations', conn)

velos['date'] = pd.to_datetime(velos['date'])

st.header("Stations avec valeurs manquantes")
missing = velos[velos['nb_total'].isna()]
if not missing.empty:
    st.dataframe(missing[['STATION_ID', 'date']].merge(stations, left_on='STATION_ID', right_on='ID')[['Nom', 'date']])
else:
    st.success("Aucune valeur manquante détectée.")

st.header("Timeline des périodes sans données")
missing_per_day = velos.groupby(velos['date'].dt.date).apply(lambda x: x['nb_total'].isna().sum())
st.line_chart(missing_per_day, use_container_width=True)
st.write("Nombre de valeurs manquantes par jour.")

st.header("Stations au comportement anormal")
anomalies = []
for sid, group in velos.groupby('STATION_ID'):
    if group['nb_total'].max() == 0:
        nom = stations[stations['ID'] == sid]['Nom'].iloc[0]
        anomalies.append(f"Station {nom} toujours vide !")
    if group['nb_total'].min() == group['nb_total'].max():
        nom = stations[stations['ID'] == sid]['Nom'].iloc[0]
        anomalies.append(f"Station {nom} valeur constante : {group['nb_total'].iloc[0]}")
if anomalies:
    for al in anomalies:
        st.warning(al)
else:
    st.success("Aucune anomalie majeure détectée.")
