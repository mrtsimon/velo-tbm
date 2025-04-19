import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import sqlite3

st.title("🚲 Occupation & Flux")

conn = sqlite3.connect('stations_velo.db')
stations = pd.read_sql_query('SELECT * FROM stations', conn)
velos = pd.read_sql_query('SELECT * FROM velos', conn)

st.header("Courbes d'occupation par station")
stations_sel = st.multiselect('Stations à comparer', stations['Nom'].unique())
if stations_sel:
    ids = stations[stations['Nom'].isin(stations_sel)]['ID']
    df = velos[velos['STATION_ID'].isin(ids)]
    df['date'] = pd.to_datetime(df['date'])
    fig = px.line(df.merge(stations, left_on='STATION_ID', right_on='ID')[['date', 'nb_total', 'Nom']], x='date', y='nb_total', color='Nom', labels={'nb_total': 'Nb vélos', 'date': 'Date'})
    st.plotly_chart(fig, use_container_width=True)

st.header("Boxplot occupation")
fig = px.box(velos.merge(stations, left_on='STATION_ID', right_on='ID'), x='Nom', y='nb_total', points='outliers')
st.plotly_chart(fig, use_container_width=True)

st.header("Carte heatmap des flux")
var_par_station = velos.groupby('STATION_ID').agg(variation=('nb_total', lambda x: x.iloc[-1] - x.iloc[0]))
var_par_station = var_par_station.reset_index().merge(stations, left_on='STATION_ID', right_on='ID')
var_par_station['color'] = var_par_station['variation'].apply(lambda var: [0,180,0,180] if var>0 else ([220,0,0,180] if var<0 else [180,180,180,120]))
var_par_station['absvar'] = var_par_station['variation'].abs()
layer_points = pdk.Layer(
    'ScatterplotLayer',
    data=var_par_station,
    get_position='[pos_x, pos_y]',
    get_color='color',
    get_radius='absvar * 10 + 100',
    pickable=True,
    auto_highlight=True,
)
midpoint = [var_par_station['pos_y'].mean(), var_par_station['pos_x'].mean()]
st.pydeck_chart(pdk.Deck(
    layers=[layer_points],
    initial_view_state=pdk.ViewState(
        latitude=midpoint[0], longitude=midpoint[1], zoom=13, pitch=0
    ),
    map_style='mapbox://styles/mapbox/light-v9'
))


