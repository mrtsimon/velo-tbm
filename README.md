# 🚲 Vélo TBM - Analyse des Stations

Ce projet analyse en temps réel les données des stations de vélos V³ (VCub) de Bordeaux Métropole, en combinant ces données avec les informations météorologiques pour fournir des analyses approfondies sur l'utilisation du système de vélos en libre-service.

## 📋 Fonctionnalités

- 🗺️ Visualisation en temps réel des stations sur une carte interactive
- 📊 Analyse des flux et de l'occupation des stations
- 🌡️ Corrélation avec les données météorologiques
- 📈 Tableaux de bord et graphiques interactifs
- 🤖 Assistant IA pour l'analyse des données
- 📥 Export des données pour analyse approfondie

## 🛠️ Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/mrtsimon/velo-tbm.git
cd velo-tbm
```

2. Créez un environnement virtuel Python :
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurez les variables d'environnement :
Créez un fichier `.env` à la racine du projet avec :
```
OPENAI_API_KEY=votre_clé_api_openai
OPENWEATHERMAP_API_KEY=votre_clé_api_météo
```

## 🚀 Utilisation

1. Lancez le collecteur de données :
```bash
python collector.py
```

2. Lancez l'application Streamlit :
```bash
streamlit run home.py
```

L'application sera accessible à l'adresse : http://localhost:8501

## 📊 Structure des Données

Le projet utilise deux bases de données SQLite :
- `stations_velo.db` : Stockage des données des stations V³
- `meteo.db` : Stockage des données météorologiques

### Tables Principales

#### stations_velo.db
- `stations` : Informations statiques sur les stations
- `velos` : Données en temps réel sur la disponibilité des vélos

#### meteo.db
- `meteo` : Données météorologiques horaires

## 🔄 Mise à jour des Données

- Le script `collector.py` récupère les données des stations V³ toutes les 2-3 minutes
- Le script `meteo.py` met à jour les données météorologiques toutes les heures

## 🛡️ Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📞 Contact

Simon - [@mrtsimon](https://github.com/mrtsimon)

Lien du projet : [https://github.com/mrtsimon/velo-tbm](https://github.com/mrtsimon/velo-tbm)
