"""
app/services/therapist_service_advanced.py

Service thérapeutique HYBRIDE - utilise les templates locaux puis enrichit
les réponses via une API gratuite (ex: HuggingFace Inference). Si aucune
clé/API disponible, retombe sur un enrichissement local plus avancé.

Sécurité & contraintes:
- Ne donne jamais de diagnostic médical
- En cas de risque élevé, recommande des actions d'urgence
"""
import os
import random
import json

try:
    import requests
except Exception:
    requests = None

from app.services.therapist_service_free import TherapistServiceFree


class TherapistServiceAdvanced:
    """Service hybride: templates locaux + API d'enrichissement (facultative).

    Configuration via variables d'environnement:
    - HF_API_KEY: clé Hugging Face Inference (optionnel)
    - HF_MODEL: nom du modèle HF (optionnel, ex: 'google/flan-t5-small')
    """

    def __init__(self, use_api=None):
        self.base = TherapistServiceFree()
        self.hf_key = os.getenv('HF_API_KEY')
        self.hf_model = os.getenv('HF_MODEL', 'google/flan-t5-small')
        # Respecter variable d'environnement USE_HF_API si fournie
        # Désactiver complètement HF: utilisation locale uniquement
        self.use_api = False
        if os.getenv('USE_HF_API', '').lower() in ('1','true','yes'):
            print("ℹ️ NOTE: HF API was requested via env, but remote enrichment is disabled by configuration.")

        # suivi du dernier enrichissement: {'timestamp': iso, 'source': 'hf'|'local', 'error': str|None}
        self.last_enrichment = None

    def get_status(self):
        """Retourne le status interne de l'enrichissement hybride."""
        return {
            'use_api_requested': bool(use_api) if 'use_api' in locals() else None,
            'hf_key_present': bool(self.hf_key),
            'hf_model': self.hf_model,
            'requests_installed': requests is not None,
            'use_api_effective': self.use_api,
            'last_enrichment': self.last_enrichment
        }

    def _build_prompt(self, base_response, conversation_history, transcription, emotion):
        # Compose un prompt court pour demander une reformulation empathique
        convo_snippet = ''
        if conversation_history:
            # garder dernières interactions pour le contexte
            last = conversation_history[-6:]
            convo_snippet = '\n'.join([f"{m['role']}: {m['content']}" for m in last if 'content' in m])

        prompt = (
            "Tu es un assistant thérapeutique empathique en français. "
            "Réécris la réponse suivante pour la rendre plus humaine, nuancée, et personnelle, "
            "sans donner de diagnostic médical, et ajoute une question de suivi ouverte à la fin.\n\n"
            f"Contexte (émotion détectée: {emotion}):\n{convo_snippet}\n\n"
            f"Transcription utilisateur: {transcription}\n\n"
            f"Réponse de base: {base_response}\n\n"
            "Réécris de façon concise (max 120 mots), ton doux et compréhensif."
        )
        return prompt

    def _call_hf(self, prompt, timeout=10):
        if not self.use_api:
            raise RuntimeError('API externe non configurée')
        headers = {"Authorization": f"Bearer {self.hf_key}", "Content-Type": "application/json"}

        # Decide which HF endpoint to call based on the model type.
        model_id = (self.hf_model or "google/flan-t5-small").strip()

        # Heuristic: if model looks like an OpenAI-compatible chat model (contains ':' or 'gpt' or 'openai/'), call chat endpoint
        is_chat_model = (':' in model_id) or ('gpt' in model_id.lower()) or model_id.startswith('openai/')

        try:
            if is_chat_model:
                url = "https://router.huggingface.co/v1/chat/completions"
                payload = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }
                resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    if "choices" in data and data["choices"]:
                        return data["choices"][0]["message"]["content"]
                    return str(data)
                else:
                    # raise to be caught below and handled as fallback
                    raise RuntimeError(f"HF API status {resp.status_code}: {resp.text}")

            else:
                # Non-chat text model: use model-specific inference endpoint
                url = f"https://api-inference.huggingface.com/models/{model_id}"
                payload = {"inputs": prompt}
                resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    # HF may return a list of generations or a dict
                    if isinstance(data, list) and data:
                        # attempt to extract generated_text or similar
                        first = data[0]
                        if isinstance(first, dict):
                            return first.get('generated_text') or first.get('summary_text') or str(first)
                        return str(first)
                    if isinstance(data, dict):
                        return data.get('generated_text') or data.get('summary_text') or json.dumps(data)
                    return str(data)
                else:
                    raise RuntimeError(f"HF API status {resp.status_code}: {resp.text}")

        except Exception as e:
            # Let caller handle fallback; propagate a clear error message
            raise RuntimeError(f"HF enrichment failed: {e}")

    def _local_enrich(self, base_response, transcription, emotion):
        # Utilise les helpers du service gratuit pour construire une réponse riche
        try:
            prefix = self.base.get_prefix(emotion)
        except Exception:
            prefix = "Je vous entends et je prends cela au sérieux."

        try:
            followup = self.base.get_followup(emotion)
        except Exception:
            followup = "Pouvez-vous m'en dire plus sur ce qui se passe?"

        try:
            long_template = self.base.get_long_template(emotion)
        except Exception:
            long_template = ''

        # Extraire sujet pour personnalisation
        subject = ''
        if transcription:
            words = [w for w in transcription.split() if len(w) > 3]
            if words:
                subject = words[0]

        # Assembler en plusieurs morceaux pour paraître naturel
        parts = []
        parts.append(prefix)
        if long_template:
            parts.append(long_template)
        # Insérer la réponse de base (template court)
        if base_response:
            parts.append(base_response)

        if subject:
            parts.append(f"Je note que vous mentionnez \"{subject}\" — merci pour ce partage.")

        parts.append(followup)

        # Joindre et normaliser espaces
        final = ' '.join([p for p in parts if p])
        final = ' '.join(final.split())
        return final.strip()

    def generate_response(self, conversation_history, emotion, transcription, is_premium=False, session_id=None):
        # Obtenir une réponse de base
        base = self.base.generate_response(conversation_history, emotion, transcription, is_premium, session_id)

        # Si API dispo, tenter d'enrichir
        if self.use_api:
            try:
                prompt = self._build_prompt(base, conversation_history, transcription, emotion)
                enriched = self._call_hf(prompt)
                if enriched:
                    self.last_enrichment = {'timestamp': __import__('datetime').datetime.utcnow().isoformat(), 'source': 'hf', 'error': None}
                    return enriched.strip()
            except Exception as e:
                # log et fallback local
                err = str(e)
                print(f"⚠️ Erreur enrichissement HF: {err}")
                self.last_enrichment = {'timestamp': __import__('datetime').datetime.utcnow().isoformat(), 'source': 'hf', 'error': err}

        # fallback local
        local_resp = self._local_enrich(base, transcription, emotion)
        # marquer que la source finale était locale (soit car api désactivée, absence de clé, ou erreur)
        if not self.last_enrichment:
            self.last_enrichment = {'timestamp': __import__('datetime').datetime.utcnow().isoformat(), 'source': 'local', 'error': None}
        else:
            # si last_enrichment existed with error, keep it; otherwise update source local
            if not self.last_enrichment.get('error'):
                self.last_enrichment['source'] = 'local'
                self.last_enrichment['timestamp'] = __import__('datetime').datetime.utcnow().isoformat()

        return local_resp

    def generate_questions(self, emotion, conversation_count, is_premium=False, session_id=None):
        # Pour l'instant on réutilise la version gratuite (templates) — on pourrait appeler l'API
        return self.base.generate_questions(emotion, conversation_count, is_premium, session_id)
