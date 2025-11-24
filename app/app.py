"""
Application Flask principale - Menthera
Psychologue virtuel 100% GRATUIT (sans GPT)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import sys
import tempfile
import traceback

# Ajouter chemin racine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charger variables d'environnement depuis .env si présent
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from app.models.user import db, User, Session
from app.services.emotion_service import EmotionService
from app.services.speech_service import SpeechToTextService
from app.services.danger_detector import DangerDetector
from app.services.therapist_service_free import TherapistServiceFree
from app.services.treatment_service import TreatmentService

def create_app():
    """Factory pour créer l'application"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///menthera.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-ME')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ Base de données initialisée")

    emotion_service = EmotionService()
    speech_service = SpeechToTextService()
    danger_detector = DangerDetector()
    therapist_service = TherapistServiceFree()
    print("Service thérapeutique basique initialisé (mode local uniquement)")
    treatment_service = TreatmentService()

    # ============================================
    # ROUTES API
    # ============================================
    @app.route('/health', methods=['GET'])
    def health():
        """Health check"""
        return jsonify({
            'status': 'ok',
            'service': 'Menthera API',
            'version': '1.0.0'
        })

    @app.route('/api/chat/process-voice', methods=['POST'])
    def process_voice():
        """Endpoint principal : analyse vocal"""
        if 'audio' not in request.files:
            return jsonify({'error': 'Pas de fichier audio'}), 400
        audio_file = request.files['audio']
        user_id = request.form.get('user_id', type=int)  # User toujours stable
        session_id = request.form.get('session_id', type=int)  # nullable

        # Sauvegarde temporaire
        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
        try:
            audio_file.save(temp_path)
            os.close(temp_fd)
            if not os.path.exists(temp_path):
                return jsonify({'error': 'Échec de sauvegarde du fichier audio'}), 500
            if os.path.getsize(temp_path) == 0:
                return jsonify({'error': 'Fichier audio vide'}), 400

            # 1. Analyse émotion
            emotion_result = emotion_service.analyze_emotion(temp_path)
            emotion = emotion_result['emotion']
            confidence = emotion_result['confidence']

            # 2. Speech-to-text
            stt_result = speech_service.audio_to_text(temp_path)
            if not stt_result['success']:
                return jsonify({'error': 'Audio incompréhensible'}), 400
            transcription = stt_result['text']

            # 3. Détection danger
            danger_analysis = danger_detector.analyze_text(transcription, emotion, confidence)

            # 4. USER: retrouvable par id (stable), email unique, multi-sessions
            user = User.query.get(user_id)
            email = f'user_{user_id}@menthera.app'
            if not user:
                user_by_email = User.query.filter_by(email=email).first()
                if user_by_email:
                    user = user_by_email
                else:
                    user = User(id=user_id, email=email, name=f'User {user_id}')
                    db.session.add(user)
                    db.session.commit()
            is_premium = user.is_premium
            limits = user.get_plan_limits()

            # 5. SESSION: existante (suite ou express), ou création nouvelle (un user → X sessions)
            if session_id:
                # suite ou express: update session d'abord
                session = Session.query.get(session_id)
                if session:
                    session.emotion_detected = emotion
                    session.confidence = confidence
                    session.danger_level = danger_analysis['danger_score']
                    db.session.commit()
                else:
                    # Si l'ID session est introuvable : création nouvelle session
                    session = Session(
                        user_id=user.id,
                        emotion_detected=emotion,
                        confidence=confidence,
                        danger_level=danger_analysis['danger_score'],
                        conversation_history=[]
                    )
                    db.session.add(session)
                    db.session.commit()
            else:
                # Créer nouvelle session normale
                session = Session(
                    user_id=user.id,
                    emotion_detected=emotion,
                    confidence=confidence,
                    danger_level=danger_analysis['danger_score'],
                    conversation_history=[]
                )
                db.session.add(session)
                db.session.commit()

            # 6. Historique/Timeline
            conversation_history = session.conversation_history or []
            conversation_history.append({
                'role': 'user',
                'content': transcription,
                'emotion': emotion,
                'timestamp': datetime.now().isoformat()
            })

            # 7. Gestion urgence
            if danger_analysis['action'] == 'URGENCE_IMMEDIATE':
                emergency_response = danger_detector.get_emergency_response(danger_analysis)
                conversation_history.append({
                    'role': 'assistant',
                    'content': emergency_response['message'],
                    'type': 'emergency',
                    'timestamp': datetime.now().isoformat()
                })
                session.conversation_history = conversation_history
                session.danger_level = danger_analysis['danger_score']
                db.session.commit()
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return jsonify({
                    'type': 'EMERGENCY',
                    'emotion': emotion,
                    'confidence': confidence,
                    'danger_analysis': danger_analysis,
                    'emergency_response': emergency_response,
                    'session_id': session.id
                })

            # 8. Réponse thérapeutique
            conversation_count = len(conversation_history) // 2
            therapist_response = therapist_service.generate_response(
                conversation_history,
                emotion,
                transcription,
                is_premium
            )
            conversation_history.append({
                'role': 'assistant',
                'content': therapist_response,
                'timestamp': datetime.now().isoformat()
            })
            session.conversation_history = conversation_history
            session.transcription = transcription
            db.session.commit()

            # 9. Questions
            questions = therapist_service.generate_questions(emotion, conversation_count, is_premium)

            # Nettoyage
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return jsonify({
                'success': True,
                'session_id': session.id,
                'emotion': emotion,
                'confidence': confidence,
                'transcription': transcription,
                'danger_analysis': danger_analysis,
                'therapist_response': therapist_response,
                'questions': questions,
                'limits': limits,
                'conversation_count': conversation_count
            })
        except Exception as e:
            if os.path.exists(temp_path):
                print(traceback.format_exc())
                try:
                    os.remove(temp_path)
                except:
                    pass
            return jsonify({'error': str(e)}), 500

    @app.route('/api/chat/end-session', methods=['POST'])
    def end_session():
        """Termine session + génère plan traitement"""
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'session_id requis'}), 400
        
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session introuvable'}), 404
        
        # CORRECTION ICI : chercher par ID d'abord, puis par email si pas trouvé
        user = User.query.get(session.user_id)
        if not user:
            # Si pas trouvé par ID, chercher par email (cas où l'ID a changé)
            email = f'user_{session.user_id}@menthera.app'
            user = User.query.filter_by(email=email).first()
            
            # Si toujours pas trouvé, créer
            if not user:
                user = User(email=email, name=f'User {session.user_id}', is_premium=False)
                db.session.add(user)
                db.session.commit()
        
        is_premium = user.is_premium
        
        # Plan de traitement
        treatment_plan = treatment_service.generate_treatment_plan(
            session.emotion_detected,
            session.danger_level,
            is_premium
        )
        
        # Résumé
        summary = therapist_service.get_summary(session.emotion_detected, session.danger_level)
        
        session.ended_at = datetime.utcnow()
        session.treatment_plan = treatment_plan
        session.diagnosis = summary
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_summary': session.to_dict(),
            'treatment_plan': treatment_plan
        })

    @app.route('/admin/hybrid-status', methods=['GET'])
    def hybrid_status():
        info = {
            'use_api_effective': getattr(therapist_service, 'use_api', False),
            'hf_key_present': bool(getattr(therapist_service, 'hf_key', None)),
            'hf_model': getattr(therapist_service, 'hf_model', None),
        }
        last = getattr(therapist_service, 'last_enrichment', None)
        info['last_enrichment'] = last
        return jsonify(info)
    return app

if __name__ == '__main__':
    app = create_app()
    print("\n" + "="*70)
    print(" MENTHERA - Psychologue Virtuel par Voix")
    print("="*70)
    print(" Modèle ML : 83.80% accuracy")
    print(" Speech-to-Text : Google (gratuit)")
    print(" 200+ questions thérapeutiques")
    print(" 50 exercices scientifiques")
    print(" 100% GRATUIT ")
    print("="*70)
    print(f" Serveur : http://localhost:5005")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=5005, debug=True)
