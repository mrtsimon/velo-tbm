import streamlit as st
import pandas as pd
import sqlite3
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt

st.title("📈 Prévisions")

conn = sqlite3.connect('stations_velo.db')
velos = pd.read_sql_query('SELECT * FROM velos', conn)
stations = pd.read_sql_query('SELECT * FROM stations', conn)

station_names = ['Toutes'] + sorted(stations['Nom'].unique())
selected_station = st.selectbox('Station à prévoir', station_names)
if selected_station != 'Toutes':
    station_id = stations[stations['Nom'] == selected_station]['ID'].iloc[0]
    df = velos[velos['STATION_ID'] == station_id].copy()
else:
    df = velos.copy()

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')
df = df.set_index('date')
serie = df['nb_total'].resample('H').mean().fillna(method='ffill')

if len(serie) < 24:
    st.warning("Pas assez de données pour faire une prévision.")
else:
    model = SARIMAX(serie, order=(1,1,1), seasonal_order=(1,1,1,24))
    results = model.fit(disp=False)
    forecast = results.get_forecast(steps=24)
    pred_uc = forecast.predicted_mean
    fig, ax = plt.subplots()
    serie.plot(ax=ax, label='Historique')
    pred_uc.plot(ax=ax, label='Prévision')
    ax.legend()
    st.pyplot(fig)
    st.write("Prévision sur les prochaines 24h.")
