
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

## Optionnel : Enrichissement via Hugging Face (API)

Le service avancé `TherapistServiceAdvanced` peut appeler l'Inference API de Hugging Face
pour reformuler et enrichir les réponses. Si vous ne fournissez pas de clé, le service retombera
sur le fallback local (aucun coût).

Configuration :

- Définir la variable d'environnement `HF_API_KEY` avec votre clé Hugging Face (optionnel).
- (Option) changer le modèle via `HF_MODEL` (ex: `google/flan-t5-small`).

Exemples (Windows bash) :

```bash
export HF_API_KEY="hf_xxx..."
export HF_MODEL="google/flan-t5-small"
python app/app.py
```

Si `HF_API_KEY` est absente, l'application fonctionnera normalement avec le moteur local.
