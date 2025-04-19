import requests
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Charger le token API de façon sécurisée
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
API_TOKEN = os.environ.get("MF_API_TOKEN")
if not API_TOKEN or API_TOKEN == "ton_token_ici":
    raise RuntimeError("Le token API n'est pas défini dans .env !")

# Calculer la date de la veille (format YYYY-MM-DD)
aujourdhui = datetime.now().date()
veille = aujourdhui - timedelta(days=1)
date_str = veille.strftime("%Y-%m-%d")

# Construire l'URL
URL = (
    f"https://www.infoclimat.fr/opendata/?version=2&method=get&format=json&stations[]=ME034"
    f"&start={date_str}&end={date_str}&token={API_TOKEN}"
)



# Requête
response = requests.get(URL)
if response.status_code != 200:
    print("Erreur lors de la récupération des données :", response.status_code, response.text)
    exit(1)

data = response.json()

# Connexion à la base SQLite
con = sqlite3.connect("meteo.db")
cur = con.cursor()

# Création de la table avec toutes les colonnes utiles
cur.execute('''CREATE TABLE IF NOT EXISTS meteo (
    id_station TEXT,
    dh_utc TEXT,
    temperature REAL,
    pression REAL,
    pression_variation_3h REAL,
    humidite REAL,
    point_de_rosee REAL,
    visibilite REAL,
    vent_moyen REAL,
    vent_rafales REAL,
    vent_rafales_10min REAL,
    vent_direction REAL,
    temperature_min REAL,
    temperature_max REAL,
    pluie_1h REAL,
    pluie_3h REAL,
    pluie_6h REAL,
    pluie_12h REAL,
    pluie_24h REAL,
    pluie_cumul_0h REAL,
    pluie_intensite REAL,
    pluie_intensite_max_1h REAL,
    uv REAL,
    complements TEXT,
    ensoleillement REAL,
    temperature_sol REAL,
    temps_omm TEXT,
    source TEXT,
    uv_index REAL,
    PRIMARY KEY (id_station, dh_utc)
)''')

# Insérer chaque enregistrement horaire
hourly = data.get("hourly", {})
for station_id, records in hourly.items():
    for record in records:
        if not isinstance(record, dict):
            continue  # Ignore tout ce qui n'est pas un dict (ex: str)
        cur.execute('''INSERT OR REPLACE INTO meteo (
            id_station, dh_utc, temperature, pression, pression_variation_3h, humidite, point_de_rosee, visibilite, vent_moyen, vent_rafales, vent_rafales_10min, vent_direction, temperature_min, temperature_max, pluie_1h, pluie_3h, pluie_6h, pluie_12h, pluie_24h, pluie_cumul_0h, pluie_intensite, pluie_intensite_max_1h, uv, complements, ensoleillement, temperature_sol, temps_omm, source, uv_index
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            record.get('id_station'),
            record.get('dh_utc'),
            float(record.get('temperature')) if record.get('temperature') not in (None, "") else None,
            float(record.get('pression')) if record.get('pression') not in (None, "") else None,
            float(record.get('pression_variation_3h')) if record.get('pression_variation_3h') not in (None, "") else None,
            float(record.get('humidite')) if record.get('humidite') not in (None, "") else None,
            float(record.get('point_de_rosee')) if record.get('point_de_rosee') not in (None, "") else None,
            float(record.get('visibilite')) if record.get('visibilite') not in (None, "") else None,
            float(record.get('vent_moyen')) if record.get('vent_moyen') not in (None, "") else None,
            float(record.get('vent_rafales')) if record.get('vent_rafales') not in (None, "") else None,
            float(record.get('vent_rafales_10min')) if record.get('vent_rafales_10min') not in (None, "") else None,
            float(record.get('vent_direction')) if record.get('vent_direction') not in (None, "") else None,
            float(record.get('temperature_min')) if record.get('temperature_min') not in (None, "") else None,
            float(record.get('temperature_max')) if record.get('temperature_max') not in (None, "") else None,
            float(record.get('pluie_1h')) if record.get('pluie_1h') not in (None, "") else None,
            float(record.get('pluie_3h')) if record.get('pluie_3h') not in (None, "") else None,
            float(record.get('pluie_6h')) if record.get('pluie_6h') not in (None, "") else None,
            float(record.get('pluie_12h')) if record.get('pluie_12h') not in (None, "") else None,
            float(record.get('pluie_24h')) if record.get('pluie_24h') not in (None, "") else None,
            float(record.get('pluie_cumul_0h')) if record.get('pluie_cumul_0h') not in (None, "") else None,
            float(record.get('pluie_intensite')) if record.get('pluie_intensite') not in (None, "") else None,
            float(record.get('pluie_intensite_max_1h')) if record.get('pluie_intensite_max_1h') not in (None, "") else None,
            float(record.get('uv')) if record.get('uv') not in (None, "") else None,
            record.get('complements'),
            float(record.get('ensoleillement')) if record.get('ensoleillement') not in (None, "") else None,
            float(record.get('temperature_sol')) if record.get('temperature_sol') not in (None, "") else None,
            record.get('temps_omm'),
            record.get('source'),
            float(record.get('uv_index')) if record.get('uv_index') not in (None, "") else None,
        ))
con.commit()
con.close()
print("Données horaires insérées dans la base meteo.db")