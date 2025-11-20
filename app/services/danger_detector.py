# app/services/danger_detector.py
import re
from app.services.data_loader import load_json


class DangerDetector:
    """Détecte le niveau de danger dans le discours.

    Améliorations:
    - Normalisation du texte (minuscules, suppression ponctuation)
    - Chargement sécurisé des ressources d'urgence via data_loader
    - Détection par patterns et poids plus explicites
    """

    CRITICAL_KEYWORDS = [
        'suicide', 'suicider', 'mort', 'mourir', 'tuer', 'finir',
        'en finir', 'disparaître', 'plus envie', 'abandonne',
        'sans issue', 'désespoir', 'désespéré'
    ]

    HIGH_RISK_KEYWORDS = [
        'dépression', 'déprimé', 'triste', 'anxieux', 'peur',
        'panique', 'angoisse', 'mal', 'souffre', 'douleur',
        'seul', 'isolé', 'personne', 'comprend'
    ]

    def __init__(self):
        self.emergency_resources = load_json('emergency_resources.json')

    def _normalize(self, text):
        if not text:
            return ''
        t = text.lower()
        t = re.sub(r"[^a-z0-9àâäéèêëïîôöùûüç\s'-]", ' ', t)
        return re.sub(r"\s+", ' ', t).strip()

    def analyze_text(self, text, emotion, confidence):
        if not text:
            return {'danger_score': 0, 'risk_level': 'FAIBLE', 'action': 'CONVERSATION_NORMALE', 'triggers': []}

        txt = self._normalize(text)
        danger_score = 0
        triggers = []

        # Critiques -> plus de poids
        for kw in self.CRITICAL_KEYWORDS:
            if kw in txt:
                danger_score += 3
                triggers.append(kw)

        # Mots à risque
        for kw in self.HIGH_RISK_KEYWORDS:
            if kw in txt:
                danger_score += 1
                triggers.append(kw)

        # Phrases longues exprimant finalité
        if any(p in txt for p in ['je veux mourir', 'j en ai marre', 'je n ai plus envie']):
            danger_score += 3
            triggers.append('phrases_finalite')

        # Ajustement par émotion et confiance
        if emotion in ['tristesse', 'peur', 'anxiete']:
            if confidence and confidence > 0.8:
                danger_score += 2
            elif confidence and confidence > 0.6:
                danger_score += 1

        danger_score = min(10, danger_score)

        if danger_score >= 8:
            risk_level = 'CRITIQUE'
            action = 'URGENCE_IMMEDIATE'
        elif danger_score >= 6:
            risk_level = 'ÉLEVÉ'
            action = 'CONSULTATION_URGENTE'
        elif danger_score >= 3:
            risk_level = 'MODÉRÉ'
            action = 'SUIVI_RECOMMANDÉ'
        else:
            risk_level = 'FAIBLE'
            action = 'CONVERSATION_NORMALE'

        return {
            'danger_score': danger_score,
            'risk_level': risk_level,
            'action': action,
            'triggers': list(dict.fromkeys(triggers))
        }

    def get_emergency_response(self, danger_analysis, country='france'):
        if danger_analysis.get('action') == 'URGENCE_IMMEDIATE':
            country_resources = self.emergency_resources.get(country, {})
            return {
                'message': "Je détecte une situation sérieuse. Votre sécurité est prioritaire.",
                'emergency_numbers': country_resources,
                'immediate_actions': [
                    "Appelez les services d'urgence locaux immédiatement",
                    "Ne restez pas seul(e) — demandez à quelqu'un de rester avec vous",
                    "Si possible, retirez tout objet dangereux autour de vous"
                ]
            }

        if danger_analysis.get('action') == 'CONSULTATION_URGENTE':
            return {
                'message': "Il serait utile de consulter un professionnel rapidement.",
                'recommendations': [
                    "Contactez un soignant ou une ligne d'écoute aujourd'hui",
                    "Demandez à un proche de vous accompagner si possible"
                ]
            }

        return None
