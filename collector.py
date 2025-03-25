import sqlite3
import json
import requests

con = sqlite3.connect('stations_velo.db')
cur = con.cursor()


resultats = requests.get('https://data.bordeaux-metropole.fr/geojson?key=B3V0LTYR77&typename=ci_vcub_p')
resultats = resultats.json()

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
    INSERT INTO velos (sation_id, nb_classiq, nb_elec, nb_total, nb_places, capacite, etat, date) 
    VALUES ({id}, {nb_classiq}, {nb_elec}, {nb_total}, {nb_places}, {capacite}, "{etat}", "{date}")
    """)
    
print(f'[{date}')
    
con.commit()
con.close()