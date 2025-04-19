import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

st.title("🌦️ Corrélations & météo")

conn = sqlite3.connect('stations_velo.db')
velos = pd.read_sql_query('SELECT * FROM velos', conn)
try:
    meteo = pd.read_sql_query('SELECT * FROM meteo', conn)
except Exception:
    st.warning("Table meteo non trouvée dans la base de données.")
    st.stop()

velos['date'] = pd.to_datetime(velos['date'])
meteo['date'] = pd.to_datetime(meteo['date'])
df = velos.merge(meteo, on='date', how='inner')

fig = px.scatter(df, x='temperature', y='nb_total', color='pluie_1h', labels={'temperature': 'Température', 'nb_total': 'Nb vélos'})
st.plotly_chart(fig, use_container_width=True)

# Heatmap de corrélation
st.header("Heatmap de corrélation (occupation, météo, flux)")
num_cols = ['nb_total', 'temperature', 'pluie_1h']
corr = df[num_cols].corr()
fig2 = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale="RdBu_r")
st.plotly_chart(fig2, use_container_width=True)
