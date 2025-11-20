# app/services/emotion_service.py
import os
import sys
import traceback

# garder compatibilité d'import dans le projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.ml.predictor import EmotionPredictor
except Exception:
    EmotionPredictor = None


class EmotionService:
    def __init__(self):
        self.predictor = None
        if EmotionPredictor:
            try:
                self.predictor = EmotionPredictor()
                print("✅ Modèle d'émotions chargé (si disponible)")
            except Exception as e:
                print(f"⚠️ Erreur chargement modèle d'émotion: {e}")
                traceback.print_exc()

    def analyze_emotion(self, audio_path):
        """Retourne dict: emotion, confidence, probabilities.

        Si le modèle n'est pas disponible, renvoie un fallback neutre.
        """
        if not self.predictor:
            return {'emotion': 'neutre', 'confidence': 0.5, 'probabilities': {}}

        try:
            result = self.predictor.predict(audio_path)
            # garantir forme stable
            return {
                'emotion': result.get('emotion', 'neutre'),
                'confidence': float(result.get('confidence', 0.5)),
                'probabilities': result.get('probabilities', {})
            }
        except Exception as e:
            print(f"⚠️ Erreur analyse émotion: {e}")
            traceback.print_exc()
            return {'emotion': 'neutre', 'confidence': 0.5, 'probabilities': {}, 'error': str(e)}
