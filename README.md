
# Menthera - Psychologue Virtuel par Voix

Système d'analyse émotionnelle et d'accompagnement psychologique 100% GRATUIT.

## Caractéristiques

- Analyse vocale (30s)
- ML Emotions : 83.80% accuracy
- Speech-to-Text gratuit
- Détection danger automatique
- 200+ questions thérapeutiques
- 50 exercices scientifiques
- 100% GRATUIT 

## Installation


# 1. Installer dépendances
pip install -r requirements.txt

# 2. Lancer le pipeline complet
python run_all.py

# OU étape par étape:
python scripts/0_download_ravdess.py
python scripts/1_organize_ravdess.py
python scripts/2_augment_data.py
python scripts/3_train_model.py
python scripts/4_test_model.py

# 3. Lancer l'API
python app/app.py

# 4. Tester l'API (autre terminal)
python test_api.py
