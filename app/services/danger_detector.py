# app/services/danger_detector.py
import json
import os

class DangerDetector:
    """Détecte le niveau de danger dans le discours"""
    
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
        # Charger ressources d'urgence
        resources_path = os.path.join('app', 'data', 'emergency_resources.json')
        try:
            with open(resources_path, 'r', encoding='utf-8') as f:
                self.emergency_resources = json.load(f)
        except:
            self.emergency_resources = {}
    
    def analyze_text(self, text, emotion, confidence):
        """Analyse le texte et retourne un niveau de danger (0-10)"""
        if not text:
            return {'danger_score': 0, 'risk_level': 'FAIBLE', 'action': 'CONVERSATION_NORMALE', 'triggers': []}
        
        text_lower = text.lower()
        danger_score = 0
        triggers = []
        
        # Vérifier mots critiques
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in text_lower:
                danger_score += 3
                triggers.append(keyword)
        
        # Vérifier mots à risque
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in text_lower:
                danger_score += 1
                triggers.append(keyword)
        
        # Analyser émotion
        if emotion in ['tristesse', 'peur', 'anxiete']:
            if confidence > 0.8:
                danger_score += 2
            elif confidence > 0.6:
                danger_score += 1
        
        danger_score = min(danger_score, 10)
        
        # Déterminer niveau
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
            'triggers': list(set(triggers))
        }
    
    def get_emergency_response(self, danger_analysis, country='france'):
        """Génère une réponse d'urgence"""
        
        if danger_analysis['action'] == 'URGENCE_IMMEDIATE':
            country_resources = self.emergency_resources.get(country, {})
            
            return {
                'message': "Je détecte que vous traversez une situation très difficile. Votre sécurité est ma priorité absolue.",
                'emergency_numbers': country_resources,
                'immediate_actions': [
                    "Appelez immédiatement le 3114 (France) ou le numéro d'urgence de votre pays",
                    "Ne restez pas seul(e), contactez un proche",
                    "Si danger immédiat, appelez le 15 (SAMU) ou le 112"
                ],
                'resources': [
                    "SOS Amitié: 09 72 39 40 50",
                    "Ligne d'écoute 24h/24"
                ]
            }
        
        elif danger_analysis['action'] == 'CONSULTATION_URGENTE':
            return {
                'message': "Je sens que vous ne vous sentez pas bien. Il serait important de consulter un professionnel rapidement.",
                'recommendations': [
                    "Prenez rendez-vous avec un psychologue dans les 48h",
                    "Parlez-en à votre médecin traitant",
                    "Contactez une ligne d'écoute si besoin"
                ]
            }
        
        else:
            return None
