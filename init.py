import sqlite3
import json
import requests

con = sqlite3.connect('stations_velo.db')
cur = con.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS stations (
    ID INTEGER PRIMARY KEY,
    Nom TEXT,
    pos_x FLOAT,
    pos_y FLOAT
);
""")


cur.execute("""
    CREATE TABLE IF NOT EXISTS velos (
    ID INTEGER PRIMARY KEY,
    STATION_ID INTEGER,
    nb_classiq INTEGER,
    nb_elec INTEGER,
    nb_total INTEGER,
    nb_places INTEGER,
    capacite INTEGER,
    etat TEXT,
    date TEXT,
    FOREIGN KEY(ID) REFERENCES stations(ID_STATION)
);
""")

resultats = requests.get('https://data.bordeaux-metropole.fr/geojson?key=B3V0LTYR77&typename=ci_vcub_p')
resultats = resultats.json()

for features in resultats["features"]:
    gid = features["properties"]["gid"]
    nom = features["properties"]["nom"]
    pos_x = features["geometry"]["coordinates"][0]
    pos_y = features["geometry"]["coordinates"][1]
        
    cur.execute(f"""
    INSERT OR REPLACE INTO stations (id, nom, pos_x, pos_y) 
    VALUES ({gid}, "{nom}", {pos_x}, {pos_y})
    """)
    
con.commit()
con.close()