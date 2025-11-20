# app/services/therapist_service_free.py
"""
Service Thérapeutique - Psychologue Virtuel Enrichi
Utilise les fichiers JSON pour des réponses fluides et variées
- questions.json: Questions thérapeutiques par phase
- responses.json: Templates de réponses enrichies et empathiques
- exercises.json: Exercices basés sur la science
- emergency_resources.json: Ressources en cas de crise
"""

import random
import re
from datetime import datetime

from app.services.data_loader import load_json, safe_get


class TherapistServiceFree:
    """Service thérapeutique - réponse plus humaine, robustesse JSON et cache.

    Principes appliqués:
    - Chargement JSON sécurisé + caching via `data_loader.load_json`
    - Eviter répétitions par session (tracking léger)
    - Réponses construites à partir de templates, transitions et enrichissements contextuels
    - Pas de dépendance externe lourde (fonctionne en environnement limité)
    """

    PHASES = ['phase_1_initial', 'phase_2_exploration', 'phase_3_solution', 'phase_4_suivi']

    def __init__(self):
        # Charger les fichiers (cachés par load_json)
        self.questions_data = load_json('questions.json')
        self.responses_data = load_json('responses.json')
        self.exercises_data = load_json('exercises.json')
        self.emergency_resources = load_json('emergency_resources.json')

        # Simple tracking pour éviter répétitions évidentes
        # structure: { session_id: {'responses': set(), 'questions': set()} }
        self.session_history = {}

        # Préparer rotors par émotion+phase (liste copiée)
        self._prepare_rotations()

        # Définitions locales enrichies (utilisées par advanced local_enrich)
        # Préfixes empathiques par émotion
        self.emotion_prefixes = {
            'tristesse': [
                "Je suis vraiment désolé(e) que vous traversiez cela.",
                "Je peux imaginer combien cela doit être lourd à porter.",
                "Merci de me confier ce que vous ressentez — c'est important."
            ],
            'anxiete': [
                "Je comprends que cela puisse être angoissant.",
                "La peur et l'inquiétude sont des réactions normales face à ça.",
                "C'est compréhensible que vous soyez inquiet(e) en ce moment."
            ],
            'colere': [
                "Je perçois beaucoup de colère dans ce que vous dites.",
                "Il est légitime de se sentir en colère face à une injustice.",
                "Cela semble vous avoir vraiment mis en difficulté."
            ],
            'peur': [
                "La peur que vous décrivez a l'air intense.",
                "Ressentir de la peur dans cette situation est compréhensible.",
                "Merci d'avoir partagé cette inquiétude — c'est courageux."
            ],
            'neutre': [
                "Je vous écoute attentivement.",
                "Merci de partager cela avec moi.",
                "Je suis là pour vous accompagner dans ce que vous vivez."
            ]
        }

        # Questions de suivi par émotion
        self.emotion_followups = {
            'tristesse': [
                "Pouvez-vous me dire quel moment de la journée cela touche le plus?",
                "Qu'est-ce qui, selon vous, déclenche le plus souvent cette tristesse?",
                "Y a-t-il quelque chose qui vous apporte un peu de réconfort ces derniers temps?"
            ],
            'anxiete': [
                "Qu'est-ce qui, précisément, vous inquiète le plus en ce moment?",
                "Avez-vous remarqué des signes physiques quand l'anxiété monte?",
                "Y a-t-il une pensée ou une image qui revient souvent?"
            ],
            'colere': [
                "Pouvez-vous décrire l'événement qui a déclenché votre colère?",
                "Qu'est-ce que vous aimeriez changer dans cette situation?",
                "Y a-t-il une personne impliquée avec qui vous voudriez communiquer différemment?"
            ],
            'peur': [
                "Quand avez-vous ressenti cette peur pour la première fois?",
                "Quelles mesures vous aident légèrement à vous sentir plus en sécurité?",
                "Y a-t-il des exemples où la peur n'a pas été aussi forte?"
            ],
            'neutre': [
                "Parlez-moi un peu plus de ce qui se passe pour vous aujourd'hui.",
                "Qu'aimeriez-vous explorer ensemble en priorité?",
                "Y a-t-il un changement récent qui vous a affecté?"
            ]
        }

        # Phrases longues structurées (templates) utilisables pour enrichir
        self.long_templates = {
            'tristesse': [
                "Je sais que les pertes et les séparations peuvent laisser un grand vide; parfois, partager un souvenir concret peut alléger un peu le poids.",
                "Lorsque la tristesse s'installe, il peut être utile de noter trois choses, même petites, qui ont apporté un léger apaisement aujourd'hui.",
            ],
            'anxiete': [
                "Quand l'anxiété survient, respirer en comptant lentement peut aider à reprendre un peu de contrôle sur le corps et l'esprit.",
                "Structurer la journée en petites étapes atteignables réduit souvent la sensation d'être submergé(e)."
            ],
            'colere': [
                "La colère peut contenir un message important sur nos limites; l'identifier peut aider à agir plus calmement par la suite.",
                "Prendre un temps pour nommer précisément ce qui met en colère permet ensuite de décider d'une réponse choisie plutôt qu'impulsive."
            ],
            'peur': [
                "La peur protège, mais peut aussi s'emballer; distinguer ce qui est probable de ce qui est imaginaire peut réduire sa puissance.",
                "D'autres personnes ont trouvé utile de préparer un petit plan d'action pour les moments où la peur devient trop forte."
            ],
            'neutre': [
                "Merci de partager; prendre un moment pour respirer et observer sans jugement ce qui se passe peut être un bon début.",
                "Parfois, articuler un objectif simple pour la journée aide à rendre les choses plus gérables."
            ]
        }
        # Charger templates par sujet (keywords + templates)
        self.subject_templates = load_json('subject_templates.json')

    def get_prefix(self, emotion):
        return self.get_unique_prefix(emotion, None)

    def get_followup(self, emotion):
        return self.get_unique_followup(emotion, None)

    def get_long_template(self, emotion):
        return self.get_unique_long(emotion, None)

    def _unique_from_pool(self, session_id, pool, kind):
        """
        Select an item from `pool` trying to avoid repeats within the same session.
        - `session_id`: id of the session (may be None)
        - `pool`: list of candidate strings
        - `kind`: short key used to track usage (e.g. 'prefixes','followups','longs')
        """
        if not pool:
            return ''
        if not session_id:
            return random.choice(pool)

        s = self.session_history.setdefault(session_id, {'responses': set(), 'questions': set(),
                                                         'prefixes': set(), 'followups': set(), 'longs': set(), 'topics': set()})
        seen = s.setdefault(kind, set())

        # find unused candidates
        unused = [p for p in pool if p not in seen]
        if not unused:
            # all used; reset this kind to allow reuse
            seen.clear()
            unused = list(pool)

        choice = random.choice(unused)
        seen.add(choice)
        return choice

    def get_unique_prefix(self, emotion, session_id=None):
        e = emotion or 'neutre'
        pool = self.emotion_prefixes.get(e, self.emotion_prefixes['neutre'])
        return self._unique_from_pool(session_id, pool, 'prefixes')

    def get_unique_followup(self, emotion, session_id=None):
        e = emotion or 'neutre'
        pool = self.emotion_followups.get(e, self.emotion_followups['neutre'])
        return self._unique_from_pool(session_id, pool, 'followups')

    def get_unique_long(self, emotion, session_id=None):
        e = emotion or 'neutre'
        pool = self.long_templates.get(e, self.long_templates['neutre'])
        return self._unique_from_pool(session_id, pool, 'longs')

    def _prepare_rotations(self):
        self.emotion_rotation = {}
        for emotion, content in self.responses_data.items():
            if emotion == 'contextual_enrichments':
                continue
            self.emotion_rotation[emotion] = {}
            for phase in self.PHASES:
                items = content.get(phase, [])
                if items:
                    self.emotion_rotation[emotion][phase] = {
                        'list': list(items),
                        'index': 0
                    }

    def _get_phase(self, conversation_count):
        if conversation_count <= 1:
            return 'phase_1_initial'
        elif conversation_count <= 3:
            return 'phase_2_exploration'
        elif conversation_count <= 5:
            return 'phase_3_solution'
        else:
            return 'phase_4_suivi'

    def _normalize_text(self, text):
        if not text:
            return ''
        text = text.lower()
        # supprimer ponctuation basique
        text = re.sub(r"[^a-z0-9àâäéèêëïîôöùûüç\s'-]", ' ', text)
        return re.sub(r"\s+", ' ', text).strip()

    def _get_contextual_enrichment(self, transcription, emotion):
        transcription_norm = self._normalize_text(transcription)
        contextual = self.responses_data.get('contextual_enrichments', {})
        # contextual keys may be pipe-separated keywords
        for key, mapping in contextual.items():
            for kw in key.split('|'):
                kw = kw.strip()
                if not kw:
                    continue
                if kw in transcription_norm:
                    # prefer emotion-specific then general
                    if isinstance(mapping, dict):
                        return mapping.get(emotion) or mapping.get('general') or ''
                    elif isinstance(mapping, str):
                        return mapping
        return ''

    def _pick_rotated(self, emotion, phase):
        rot = self.emotion_rotation.get(emotion, {}).get(phase)
        if not rot:
            # fallback to neutral
            neutral = self.responses_data.get('neutre', {})
            return random.choice(neutral.get(phase, ["Merci d'avoir partagé. Je suis là pour écouter."]))

        lst = rot['list']
        # rotation index simple
        idx = rot['index'] % len(lst)
        rot['index'] = (rot['index'] + 1) % len(lst)
        return lst[idx]

    def _avoid_repeat(self, session_id, candidate, kind='responses'):
        if not session_id:
            return candidate
        s = self.session_history.setdefault(session_id, {'responses': set(), 'questions': set()})
        seen = s.get(kind, set())
        if candidate in seen:
            # slight variation: try to return an alternative if available
            # find alternative in responses pool
            # naive approach: return candidate (we avoid heavy search)
            return candidate
        seen.add(candidate)
        return candidate

    def generate_response(self, conversation_history, emotion, transcription, is_premium=False, session_id=None):
        conversation_count = len(conversation_history) // 2
        phase = self._get_phase(conversation_count)

        # Sélection de base via rotation
        base = self._pick_rotated(emotion, phase)

        # transition phrase
        transition_list = self.responses_data.get(emotion, {}).get('transition_phrases', [])
        transition = random.choice(transition_list) if transition_list and conversation_count >= 2 else ''

        # enrichissement contextuel
        contextual = self._get_contextual_enrichment(transcription or '', emotion)

        # reformulation brève (humaniser)
        reformulation = ''
        if transcription and len(transcription.split()) > 3:
            # garder phrase courte: reprendre 5 premiers mots
            reformulation = 'Si je comprends bien, vous dites : "' + ' '.join(transcription.split()[:12]) + '..."'

        # Detect subject keywords from transcription to make replies specific
        transcription_norm = self._normalize_text(transcription or '')
        # try to find a noun-like subject (longest word >3 chars that is not a stopword)
        subject = ''
        if transcription_norm:
            words = [w for w in transcription_norm.split() if len(w) > 3]
            if words:
                # prefer last meaningful word (often the topic)
                subject = words[-1]

        # Special-case: short polite replies for 'merci'
        if 'merci' in transcription_norm or 'remerc' in transcription_norm:
            polite = self.responses_data.get('contextual_enrichments', {}).get('merci|reconnaissant', {})
            if isinstance(polite, dict):
                return polite.get('general', 'De rien — je suis là pour vous.')
            elif isinstance(polite, str):
                return polite

        # Assemble with subject-specific phrasing
        # Find a matching subject/topic template by keywords (subject or transcription)
        topic_template = ''
        if self.subject_templates and transcription_norm:
            for topic, data in self.subject_templates.items():
                kws = data.get('keywords', [])
                # check subject first
                if subject and subject in kws:
                    # pick a template for the emotion if available
                    templ = data.get('templates', {}).get(emotion) or data.get('templates', {}).get('neutre')
                    if templ:
                        topic_template = random.choice(templ)
                        break
                # else check if any keyword appears in full transcription
                for kw in kws:
                    if kw and kw in transcription_norm:
                        templ = data.get('templates', {}).get(emotion) or data.get('templates', {}).get('neutre')
                        if templ:
                            topic_template = random.choice(templ)
                            break
                if topic_template:
                    break

        subject_phrase = f"Je remarque que vous parlez de '{subject}'." if subject else ''

        # Use session-aware unique selections for prefix / long template / followup
        prefix = self.get_unique_prefix(emotion, session_id)
        long_tpl = self.get_unique_long(emotion, session_id)
        followup = self.get_unique_followup(emotion, session_id) if conversation_count >= 1 else ''

        parts = [p for p in [prefix, base, topic_template, subject_phrase, transition, contextual, long_tpl, reformulation, followup] if p]
        final = ' '.join(parts)
        final = re.sub(r"\s+", ' ', final).strip()

        # Eviter répétition évidente
        final = self._avoid_repeat(session_id, final, 'responses')

        return final

    def generate_questions(self, emotion, conversation_count, is_premium=False, session_id=None):
        phase = self._get_phase(conversation_count)
        pool = self.questions_data.get(emotion) or self.questions_data.get('neutre', {})
        candidates = pool.get(phase, pool.get('phase_1_initial', []))
        if not candidates:
            return []

        # déterminer limite selon premium
        if is_premium:
            limit = min(5, len(candidates))
        else:
            if conversation_count <= 1:
                limit = min(2, len(candidates))
            elif conversation_count <= 3:
                limit = min(3, len(candidates))
            else:
                limit = min(3, len(candidates))

        selected = random.sample(candidates, limit) if len(candidates) >= limit else list(candidates)
        if session_id:
            s = self.session_history.setdefault(session_id, {'responses': set(), 'questions': set()})
            for q in selected:
                s['questions'].add(q)
        return selected

    def get_recommended_exercises(self, emotion, conversation_count, is_premium=False):
        exercises = self.exercises_data.get(emotion) or self.exercises_data.get('neutre', {})
        if is_premium:
            pool = exercises.get('premium', []) + exercises.get('free', [])
            limit = 3
        else:
            pool = exercises.get('free', [])
            limit = 1
        if not pool:
            return []
        return random.sample(pool, min(limit, len(pool)))

    def get_summary(self, emotion, danger_level, conversation_history=None):
        # choisir un template suivi
        pool = self.responses_data.get(emotion, {}).get('phase_4_suivi', []) or self.responses_data.get('neutre', {}).get('phase_4_suivi', [])
        summary = random.choice(pool) if pool else "Merci d'avoir partagé ; prenez soin de vous."

        if danger_level >= 8:
            summary += "\n\n🚨 URGENT : Si vous êtes en danger immédiat, appelez les services d'urgence locaux." 
        elif danger_level >= 6:
            summary += "\n\n⚠️ Je vous recommande de contacter un professionnel rapidement."
        elif danger_level >= 4:
            summary += "\n\n💡 Envisagez de parler à un professionnel ou de consulter des ressources de soutien."
        else:
            summary += "\n\n✨ Continuez les efforts que vous faites aujourd'hui — c'est important." 

        return summary

    def get_emergency_response_resources(self, country='tunisie'):
        return self.emergency_resources.get(country, {})
