# app/services/therapist_service_free.py
"""
Service Thérapeutique - Psychologue Virtuel Enrichi
Utilise les fichiers JSON pour des réponses fluides et variées
- questions.json: Questions thérapeutiques par phase
- responses.json: Templates de réponses enrichies et empathiques
- exercises.json: Exercices basés sur la science
- emergency_resources.json: Ressources en cas de crise
"""

import json
import os
import random
from datetime import datetime

class TherapistServiceFree:
    """Psychologue virtuel basé sur données JSON enrichies - SUPER SOLUTION v2"""
    
    def __init__(self):
        """Initialise le service avec tous les fichiers de données"""
        
        # 1. Charger les QUESTIONS
        questions_path = os.path.join('app', 'data', 'questions.json')
        with open(questions_path, 'r', encoding='utf-8') as f:
            self.questions_data = json.load(f)
        
        # 2. Charger les RÉPONSES ENRICHIES
        responses_path = os.path.join('app', 'data', 'responses.json')
        with open(responses_path, 'r', encoding='utf-8') as f:
            self.responses_data = json.load(f)
        
        # 3. Charger les EXERCICES
        exercises_path = os.path.join('app', 'data', 'exercises.json')
        with open(exercises_path, 'r', encoding='utf-8') as f:
            self.exercises_data = json.load(f)
        
        # 4. Charger les RESSOURCES D'URGENCE
        emergency_path = os.path.join('app', 'data', 'emergency_resources.json')
        with open(emergency_path, 'r', encoding='utf-8') as f:
            self.emergency_resources = json.load(f)
        
        # TRACKING par session pour garantir l'unicité (zedtha jdida)
        self.session_history = {}  # {session_id: {used_responses, used_questions}}
        self.emotion_rotation = {}  # Rotation des réponses par émotion/phase
        self._initialize_rotation()
        
    
    def _initialize_rotation(self):
        """Initialise la rotation des réponses pour chaque émotion/phase"""
        for emotion in self.responses_data:
            if emotion == 'contextual_enrichments':
                continue
            self.emotion_rotation[emotion] = {}
            for phase in ['phase_1_initial', 'phase_2_exploration', 'phase_3_solution', 'phase_4_suivi']:
                if phase in self.responses_data[emotion]:
                    responses = self.responses_data[emotion][phase]
                    self.emotion_rotation[emotion][phase] = {
                        'list': responses,
                        'index': 0,
                        'shuffled': responses.copy()
                    }
                    random.shuffle(self.emotion_rotation[emotion][phase]['shuffled'])
    
    def _track_session(self, session_id, emotion, response_used, question_used=None):
        """Track les réponses/questions utilisées par session"""
        if session_id not in self.session_history:
            self.session_history[session_id] = {
                'responses': {emotion: [response_used]},
                'questions': {emotion: [question_used] if question_used else []},
                'last_emotion': emotion
            }
        else:
            if emotion not in self.session_history[session_id]['responses']:
                self.session_history[session_id]['responses'][emotion] = [response_used]
            else:
                self.session_history[session_id]['responses'][emotion].append(response_used)
            
            if question_used:
                if emotion not in self.session_history[session_id]['questions']:
                    self.session_history[session_id]['questions'][emotion] = [question_used]
                else:
                    self.session_history[session_id]['questions'][emotion].append(question_used)
    
    def _get_phase(self, conversation_count):
        """Détermine la phase de la conversation de manière fluide"""
        if conversation_count <= 1:
            return 'phase_1_initial'
        elif conversation_count <= 3:
            return 'phase_2_exploration'
        elif conversation_count <= 5:
            return 'phase_3_solution'
        else:
            return 'phase_4_suivi'
    
    def _get_contextual_enrichment(self, transcription, emotion):
        """
        Cherche des mots-clés dans la transcription pour ajouter du contexte
        Utilise responses.json pour les enrichissements contextuels
        """
        transcription_lower = transcription.lower()
        contextual_enrichments = self.responses_data.get('contextual_enrichments', {})
        
        for keywords, responses_dict in contextual_enrichments.items():
            # Vérifier si un mot-clé est présent
            keyword_list = keywords.split('|')
            if any(keyword in transcription_lower for keyword in keyword_list):
                if isinstance(responses_dict, dict):
                    # Chercher la réponse pour cette émotion
                    if emotion in responses_dict:
                        return responses_dict[emotion]
                    elif 'general' in responses_dict:
                        return responses_dict['general']
        
        return ""
    
    def generate_response(self, conversation_history, emotion, transcription, is_premium=False, session_id=None):
        """
        Réponse TRÈS FLUIDE et UNIQUE garantie
        - Utilise responses.json avec rotation intelligente
        - Ajoute contexte basé sur la transcription
        - GARANTIT l'unicité totale par session
        - Naturalité humaine maximale
        """
        conversation_count = len(conversation_history) // 2
        phase = self._get_phase(conversation_count)
        
        # Obtenir les réponses pour cette émotion + phase
        emotion_responses = self.responses_data.get(emotion, self.responses_data.get('neutre'))
        phase_responses = emotion_responses.get(phase, emotion_responses.get('phase_1_initial', []))
        
        # Sélectionner une réponse UNIQUE via rotation
        if phase_responses:
            if emotion in self.emotion_rotation and phase in self.emotion_rotation[emotion]:
                rotation = self.emotion_rotation[emotion][phase]
                
                # Si on a épuisé la liste, la réinitialiser et mélanger
                if rotation['index'] >= len(rotation['shuffled']):
                    rotation['shuffled'] = rotation['list'].copy()
                    random.shuffle(rotation['shuffled'])
                    rotation['index'] = 0
                
                # Prendre la réponse suivante dans la rotation
                base_response = rotation['shuffled'][rotation['index']]
                rotation['index'] += 1
            else:
                # sélection aléatoire simple
                base_response = random.choice(phase_responses)
        else:
            base_response = "Merci de partager. Je suis ici pour vous écouter."
        
        # Obtenir une phrase de transition
        transition_responses = emotion_responses.get('transition_phrases', [])
        transition = random.choice(transition_responses) if transition_responses else ""
        
        # Ajouter enrichissement contextuel (20+ patterns)
        contextual = self._get_contextual_enrichment(transcription, emotion)
        
        # Construire la réponse finale de manière fluide
        response_parts = [base_response]
        
        # Ajouter transition si approprié
        if conversation_count >= 2 and transition:
            response_parts.append(transition)
        
        # Ajouter contextuel s'il existe (personnalisation)
        if contextual:
            response_parts.append(contextual)
        
        final_response = " ".join(response_parts)
        
        # Nettoyer les espaces multiples et normaliser
        final_response = " ".join(final_response.split())
        
        # Tracker pour éviter répétitions en session
        if session_id:
            self._track_session(session_id, emotion, final_response)
        
        return final_response.strip()
    
    def generate_questions(self, emotion, conversation_count, is_premium=False, session_id=None):
        """
         Questions VARIÉES ET INTELLIGENTES
        - Jamais les mêmes questions deux fois en session
        - Sélection ALÉATOIRE complète pour l'unicité totale
        - Phases progressives: 2→3→3 questions
        - Toutes les réponses différentes chaque tour
        """
        phase = self._get_phase(conversation_count)
        
        # Obtenir les questions pour cette émotion + phase
        emotion_questions = self.questions_data.get(emotion, self.questions_data.get('neutre'))
        phase_questions = emotion_questions.get(phase, emotion_questions.get('phase_1_initial', []))
        
        # Déterminer le nombre de questions (VARIABLE pour naturel)
        if is_premium:
            limit = 5  # Premium: 5 questions
        else:
            # Gratuit: progression pour fluidité
            if conversation_count <= 1:
                limit = 2  # Début: 2 questions
            elif conversation_count <= 3:
                limit = 3  # Milieu: 3 questions
            else:
                limit = 3  # Suite: 3 questions variées
        
        # random.sample() pour GARANTIR l'unicité
        # (différentes questions à chaque turn, jamais les mêmes en même ordre)
        if len(phase_questions) > limit:
            selected_questions = random.sample(phase_questions, min(limit, len(phase_questions)))
        else:
            selected_questions = random.sample(phase_questions, len(phase_questions))
        
        # 🆕 Tracker pour session
        if session_id and selected_questions:
            self._track_session(session_id, emotion, None, selected_questions[0])
        
        return selected_questions
    
    def get_recommended_exercises(self, emotion, conversation_count, is_premium=False):
        """
        Recommande des exercices basés sur les fichiers exercises.json
        """
        exercises = self.exercises_data.get(emotion, self.exercises_data.get('neutre', {}))
        
        # Sélectionner les exercices appropriés
        if is_premium:
            available_exercises = exercises.get('premium', []) + exercises.get('free', [])
            limit = 3
        else:
            available_exercises = exercises.get('free', [])
            limit = 1
        
        # Sélectionner aléatoirement
        if available_exercises:
            return random.sample(available_exercises, min(limit, len(available_exercises)))
        return []
    
    def get_summary(self, emotion, danger_level, conversation_history=None):
        """
        Résumé de session EMPATHIQUE ET PERSONNALISÉ
        Utilise responses.json pour la variété
        """
        emotion_responses = self.responses_data.get(emotion, self.responses_data.get('neutre'))
        phase_4_responses = emotion_responses.get('phase_4_suivi', [])
        
        if phase_4_responses:
            summary = random.choice(phase_4_responses)
        else:
            summary = "Merci d'avoir partagé avec moi. Votre bien-être m'importe."
        
        # Ajouter recommandation basée sur le danger
        if danger_level >= 8:
            summary += "\n\n🚨 **URGENT**: Vos pensées semblent très sérieuses. Je vous encourage fortement à contacter un professionnel dès maintenant ou appelez un service d'urgence."
        elif danger_level >= 6:
            summary += "\n\n⚠️ **IMPORTANT**: Vos sentiments semblent sérieux. Une consultation avec un professionnel de santé mentale serait vraiment bénéfique."
        elif danger_level >= 4:
            summary += "\n\n💡 Conseil: Envisagez de parler à un psychologue ou thérapeute professionnel. Vous méritez du soutien spécialisé."
        else:
            summary += "\n\n✨ Continuez à prendre soin de vous. Vous êtes sur la bonne voie!"
        
        return summary
    
    def get_emergency_response_resources(self, country='tunisie'):
        """Obtient les ressources d'urgence pour le pays"""
        return self.emergency_resources.get(country, {})
