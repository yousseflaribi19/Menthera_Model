# app/services/therapist_service_free.py
import json
import os

class TherapistServiceFree:
    """Psychologue virtuel basé sur templates (gratuit)"""
    
    def __init__(self):
        # Charger questions
        questions_path = os.path.join('app', 'data', 'questions.json')
        with open(questions_path, 'r', encoding='utf-8') as f:
            self.questions_data = json.load(f)
        
        # Templates de réponses simples
        self.response_templates = {
            'tristesse': [
                "Je comprends que vous traversez un moment difficile. La tristesse est une émotion normale.",
                "Merci de partager ce que vous ressentez. Votre tristesse mérite d'être écoutée."
            ],
            'anxiete': [
                "Je perçois de l'anxiété dans votre voix. C'est une réaction normale face au stress.",
                "L'anxiété peut être difficile. Je suis là pour vous aider."
            ],
            'colere': [
                "Je perçois de la colère. Cette émotion mérite d'être exprimée de façon constructive.",
                "La colère est normale. Parlons de ce qui vous met dans cet état."
            ],
            'peur': [
                "Je sens que vous avez peur. C'est une émotion protectrice.",
                "La peur que vous ressentez est réelle. Parlons-en ensemble."
            ],
            'neutre': [
                "Bienvenue. Je suis ici pour vous écouter.",
                "Merci de prendre ce temps pour vous."
            ]
        }
    
    def generate_response(self, conversation_history, emotion, transcription, is_premium=False):
        """Génère une réponse basée sur templates"""
        conversation_count = len(conversation_history) // 2
        templates = self.response_templates.get(emotion, self.response_templates['neutre'])
        response = templates[conversation_count % len(templates)]
        
        # Personnalisation simple
        if 'seul' in transcription.lower():
            response += " Vous n'êtes pas seul(e)."
        
        return response
    
    def generate_questions(self, emotion, conversation_count, is_premium=False):
        """Génère des questions de suivi"""
        # Déterminer phase
        if conversation_count <= 3:
            phase = 'phase_1_initial'
        elif conversation_count <= 7:
            phase = 'phase_2_exploration'
        else:
            phase = 'phase_3_solution'
        
        emotion_questions = self.questions_data.get(emotion, self.questions_data['neutre'])
        phase_questions = emotion_questions.get(phase, emotion_questions['phase_1_initial'])
        
        limit = 5 if is_premium else 2
        return phase_questions[:limit]
    
    def get_summary(self, emotion, danger_level):
        """Résumé de session"""
        summaries = {
            'tristesse': "Vous traversez une période de tristesse. C'est une émotion normale.",
            'anxiete': "Vous ressentez de l'anxiété. Des techniques peuvent vous aider.",
            'colere': "La colère que vous ressentez est légitime.",
            'peur': "Votre peur est réelle et compréhensible.",
            'neutre': "Vous semblez en équilibre."
        }
        
        summary = summaries.get(emotion, summaries['neutre'])
        
        if danger_level >= 6:
            summary += " ⚠️ Consultez un professionnel rapidement."
        
        return summary
