import pandas as pd
import sqlite3
from datetime import datetime

def extract_hour_minute(date_str):
    """Extrait l'heure et la minute d'une chaîne de date ISO."""
    dt = pd.to_datetime(date_str)
    return dt.hour, dt.minute

def load_velo_data():
    conn = sqlite3.connect('stations_velo.db')
    velos = pd.read_sql_query('SELECT * FROM velos', conn)
    conn.close()
    velos['hour'], velos['minute'] = zip(*velos['date'].map(extract_hour_minute))
    return velos

def load_meteo_data():
    conn = sqlite3.connect('meteo.db')
    meteo = pd.read_sql_query('SELECT * FROM meteo', conn)
    conn.close()
    meteo['hour'], meteo['minute'] = zip(*meteo['dh_utc'].map(extract_hour_minute))
    return meteo

def join_velo_meteo():
    velos = load_velo_data()
    meteo = load_meteo_data()
    # Join sur date (heure+minute) la plus proche
    merged = pd.merge_asof(
        velos.sort_values('date'),
        meteo.sort_values('dh_utc'),
        left_on=['date'],
        right_on=['dh_utc'],
        direction='nearest',
        tolerance=pd.Timedelta('10m') # tolérance de 10 minutes
    )
    # Garder les colonnes météo utiles
    keep_cols = ['temperature', 'humidite', 'vent_moyen', 'pluie_1h']
    for col in keep_cols:
        merged[col] = merged[col]
    return merged

if __name__ == '__main__':
    merged = join_velo_meteo()
    print(merged[['STATION_ID', 'date', 'temperature', 'humidite', 'vent_moyen', 'pluie_1h']].head())
