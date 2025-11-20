import json
import os
from functools import lru_cache


@lru_cache(maxsize=16)
def load_json(path):
    """Charge un fichier JSON depuis `app/data/` de façon sûre et cache le résultat.

    Retourne un dict vide en cas d'erreur, et loggue l'exception.
    """
    try:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base, 'data', path)
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        # Ne pas faire planter l'app pour un JSON manquant; renvoyer dictionnaire vide
        print(f"⚠️ load_json erreur pour {path}: {e}")
        return {}


def safe_get(dct, *keys, default=None):
    """Récupère un chemin de clés depuis un dict imbriqué, retourne default si absent."""
    cur = dct
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur
