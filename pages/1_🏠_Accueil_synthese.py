import streamlit as st
import pandas as pd
import sqlite3

st.title("🏠 Accueil / Synthèse")

conn = sqlite3.connect('stations_velo.db')
stations = pd.read_sql_query('SELECT * FROM stations', conn)
velos = pd.read_sql_query('SELECT * FROM velos', conn)

st.header("KPIs globaux")
st.metric("Nombre de stations", len(stations))
st.metric("Nombre d'enregistrements vélos", len(velos))
st.metric("Taux d'occupation moyen", f"{velos['nb_total'].mean():.1f} vélos")

# Correction conversion pour la colonne date
velos['date'] = pd.to_datetime(velos['date'], errors='coerce')
velos_valid = velos[pd.to_datetime(velos['date'], errors='coerce').notnull()].copy()
velos_valid['date'] = pd.to_datetime(velos_valid['date'], errors='coerce')

st.header("Evolution du nombre de vélos (tous stations)")
df_evol = velos_valid.groupby(velos_valid['date'].dt.date)['nb_total'].sum().reset_index()
st.line_chart(df_evol.set_index('date'), use_container_width=True)

st.header("Alertes automatiques")
# Station toujours pleine/vide
alertes = []
for sid, group in velos.groupby('STATION_ID'):
    if group['nb_total'].max() == 0:
        nom = stations[stations['ID'] == sid]['Nom'].iloc[0]
        alertes.append(f"🚨 Station {nom} toujours vide !")
    if group['nb_total'].min() == group['nb_total'].max():
        nom = stations[stations['ID'] == sid]['Nom'].iloc[0]
        alertes.append(f"⚠️ Station {nom} valeur constante : {group['nb_total'].iloc[0]}")
if alertes:
    for al in alertes:
        st.warning(al)
else:
    st.success("Aucune anomalie majeure détectée.")
