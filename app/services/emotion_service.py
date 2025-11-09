# app/services/emotion_service.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ml.predictor import EmotionPredictor  # ← Changement ici

class EmotionService:
    def __init__(self):
        try:
            self.predictor = EmotionPredictor()
            print("✅ Modèle d'émotions chargé (83.80% accuracy)")
        except Exception as e:
            print(f"⚠️ Erreur chargement modèle: {e}")
            self.predictor = None
    
    def analyze_emotion(self, audio_path):
        if not self.predictor:
            return {
                'emotion': 'neutre',
                'confidence': 0.5,
                'all_probabilities': {}
            }
        
        try:
            result = self.predictor.predict(audio_path)
            return {
                'emotion': result['emotion'],
                'confidence': result['confidence'],
                'all_probabilities': result['probabilities']
            }
        except Exception as e:
            print(f"⚠️ Erreur analyse émotion: {e}")
            return {
                'emotion': 'neutre',
                'confidence': 0.5,
                'all_probabilities': {},
                'error': str(e)
            }
