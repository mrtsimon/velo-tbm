#!/usr/bin/env python3
import sqlite3
import json
import requests
import os

# Utiliser un chemin absolu pour la base de données
db_path = os.path.join('/home/simon/velo-tbm', 'stations_velo.db')
print(f"Connexion à la base de données: {db_path}")

con = sqlite3.connect(db_path)
cur = con.cursor()

try:
    resultats = requests.get('https://data.bordeaux-metropole.fr/geojson?key=B3V0LTYR77&typename=ci_vcub_p')
    resultats = resultats.json()
    
    count = 0
    for features in resultats["features"]:
        id = features["properties"]["gid"]
        nb_classiq = features["properties"]["nbclassiq"]
        nb_elec = features["properties"]["nbelec"]
        nb_total = features["properties"]["nbvelos"]
        nb_places = features["properties"]["nbplaces"]
        capacite = nb_places + nb_total
        etat = features["properties"]["etat"]
        date = features["properties"]["mdate"]
            
        cur.execute(f"""
        INSERT INTO velos (station_id, nb_classiq, nb_elec, nb_total, nb_places, capacite, etat, date) 
        VALUES ({id}, {nb_classiq}, {nb_elec}, {nb_total}, {nb_places}, {capacite}, "{etat}", "{date}")
        """)
        count += 1
    
    print(f'Collector executé avec succès : {date}, {count} stations ajoutées')
    
except Exception as e:
    print(f"Erreur lors de l'exécution du collector: {e}")
finally:
    con.commit()
    con.close()