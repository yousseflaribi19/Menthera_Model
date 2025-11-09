# app/services/treatment_service.py
import json
import os

class TreatmentService:
    def __init__(self):
        exercises_path = os.path.join('app', 'data', 'exercises.json')
        with open(exercises_path, 'r', encoding='utf-8') as f:
            self.exercises = json.load(f)
    
    def generate_treatment_plan(self, emotion, danger_level, is_premium=False):
        emotion_exercises = self.exercises.get(emotion, self.exercises['tristesse'])
        
        if is_premium:
            selected = emotion_exercises['free'] + emotion_exercises['premium'][:12]
        else:
            selected = emotion_exercises['free']
        
        return {
            'emotion': emotion,
            'danger_level': danger_level,
            'plan_type': 'PREMIUM' if is_premium else 'GRATUIT',
            'exercises': selected,
            'recommendations': self._get_recommendations(danger_level, is_premium)
        }
    
    def _get_recommendations(self, danger_level, is_premium):
        base = [
            "Maintenez une routine quotidienne",
            "Pratiquez une activité physique régulière",
            "Gardez contact avec vos proches",
            "Dormez 7-8 heures par nuit",
            "Limitez alcool et caféine"
        ]
        
        if is_premium:
            base.extend([
                "Suivez les exercices premium quotidiennement",
                "Consultez les ressources avancées",
                "Utilisez l'application de suivi"
            ])
        
        if danger_level >= 6:
            base.insert(0, "⚠️ IMPORTANT: Consultez un professionnel rapidement")
        
        return base
