# app/app.py
"""
Application Flask principale - Menthera
Psychologue virtuel
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import sys
import traceback

# Ajouter chemin racine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import db, User, Session
from app.services.emotion_service import EmotionService
from app.services.speech_service import SpeechToTextService
from app.services.danger_detector import DangerDetector
from app.services.therapist_service_free import TherapistServiceFree
from app.services.treatment_service import TreatmentService


def create_app():
    """Factory pour créer l'application"""
    
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///menthera.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-ME')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
    
    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Init DB
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("✅ Base de données initialisée")
    
    # Init services
    emotion_service = EmotionService()
    speech_service = SpeechToTextService()
    danger_detector = DangerDetector()
    therapist_service = TherapistServiceFree()
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
        temp_path = None
        
        try:
            # LOGS DE DEBUG COMPLETS
            print("\n" + "="*60)
            print("REQUÊTE REÇUE - DÉTAILS COMPLETS")
            print("="*60)
            print(f"✓ Files reçus: {list(request.files.keys())}")
            print(f"✓ Form data: {dict(request.form)}")
            print(f"✓ Content-Type: {request.content_type}")
            print("="*60 + "\n")
            
            # Validation fichier audio
            if 'audio' not in request.files:
                print("❌ ERREUR: Clé 'audio' manquante dans request.files")
                print(f"   Clés disponibles: {list(request.files.keys())}")
                return jsonify({'error': 'Pas de fichier audio', 'files_received': list(request.files.keys())}), 400
            
            audio_file = request.files['audio']
            
            # Vérifier que le fichier n'est pas vide
            if audio_file.filename == '':
                print("❌ ERREUR: Nom de fichier vide")
                return jsonify({'error': 'Fichier audio vide'}), 400
            
            print(f"✅ Fichier audio: {audio_file.filename}")
            
            # Validation user_id
            user_id_str = request.form.get('user_id', None)
            session_id_str = request.form.get('session_id', None)
            
            print(f"✅ user_id (str): '{user_id_str}' (type: {type(user_id_str)})")
            print(f"✅ session_id (str): '{session_id_str}'")
            
            if not user_id_str:
                print("❌ ERREUR: user_id manquant")
                return jsonify({'error': 'user_id requis'}), 400
            
            # Conversion user_id en int
            try:
                user_id = int(user_id_str)
                print(f"✅ user_id converti: {user_id} (int)")
            except ValueError as e:
                print(f"❌ ERREUR: Conversion user_id impossible: {e}")
                return jsonify({'error': 'user_id doit être un entier'}), 400
            
            # Sauvegarder temporairement
            temp_path = f'temp_{user_id}_{datetime.now().timestamp()}.wav'
            audio_file.save(temp_path)
            print(f"✅ Fichier sauvegardé: {temp_path}")
            
            # Vérifier que le fichier existe
            if not os.path.exists(temp_path):
                print(f"❌ ERREUR: Fichier non créé: {temp_path}")
                return jsonify({'error': 'Erreur sauvegarde fichier'}), 500
            
            file_size = os.path.getsize(temp_path)
            print(f"✅ Taille fichier sur disque: {file_size} bytes")
            
            if file_size == 0:
                print("❌ ERREUR: Fichier vide sur disque")
                os.remove(temp_path)
                return jsonify({'error': 'Fichier audio vide'}), 400
            
            # 1. ANALYSE ÉMOTION
            print("\nAnalyse émotion...")
            emotion_result = emotion_service.analyze_emotion(temp_path)
            emotion = emotion_result['emotion']
            confidence = emotion_result['confidence']
            print(f"✅ Émotion: {emotion} (confiance: {confidence:.2%})")
            
            # 2. SPEECH-TO-TEXT
            print("\n Speech-to-text...")
            stt_result = speech_service.audio_to_text(temp_path)
            
            if not stt_result['success']:
                print(f"❌ ERREUR STT: {stt_result.get('error', 'Inconnu')}")
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                return jsonify({'error': 'Audio incompréhensible', 'stt_error': stt_result.get('error')}), 400
            
            transcription = stt_result['text']
            print(f"✅ Transcription: {transcription[:100]}...")
            
            # 3. DÉTECTION DANGER
            print("\n⚠️  Analyse danger...")
            danger_analysis = danger_detector.analyze_text(transcription, emotion, confidence)
            print(f"✅ Score danger: {danger_analysis['danger_score']}/10")
            
            # 4. USER
            print(f"\n👤 Recherche utilisateur {user_id}...")
            user = db.session.get(User, user_id)
            
            if not user:
                print(f"✅ Création nouvel utilisateur {user_id}")
                user = User(id=user_id, email=f'user_{user_id}@menthera.app', name=f'User {user_id}')
                db.session.add(user)
                db.session.commit()
            else:
                print(f"✅ Utilisateur trouvé: {user.email}")
            
            is_premium = user.is_premium
            limits = user.get_plan_limits()
            print(f"✅ Premium: {is_premium}")
            
            # 5. SESSION
            print(f"\n📋 Gestion session...")
            session = None
            
            if session_id_str:
                try:
                    session_id_int = int(session_id_str)
                    session = db.session.get(Session, session_id_int)
                    if session:
                        print(f"✅ Session trouvée: {session_id_int}")
                    else:
                        print(f"⚠️  Session {session_id_int} introuvable")
                except (ValueError, TypeError) as e:
                    print(f"⚠️  session_id invalide: {e}")
            
            if not session:
                print("✅ Création nouvelle session")
                session = Session(
                    user_id=user_id,
                    emotion_detected=emotion,
                    confidence=confidence,
                    danger_level=danger_analysis['danger_score'],
                    conversation_history=[]
                )
                db.session.add(session)
                db.session.commit()
                print(f"✅ Session créée: ID={session.id}")
            
            # 6. HISTORIQUE
            conversation_history = session.conversation_history or []
            conversation_history.append({
                'role': 'user',
                'content': transcription,
                'emotion': emotion,
                'timestamp': datetime.now().isoformat()
            })
            
            # 7. URGENCE ?
            if danger_analysis.get('action') == 'URGENCE_IMMEDIATE':
                print("\n🚨 URGENCE DÉTECTÉE")
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
                
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
                
                return jsonify({
                    'type': 'EMERGENCY',
                    'emotion': emotion,
                    'confidence': confidence,
                    'danger_analysis': danger_analysis,
                    'emergency_response': emergency_response,
                    'session_id': session.id
                })
            
            # 8. RÉPONSE THÉRAPEUTIQUE
            print("\n💬 Génération réponse thérapeutique...")
            conversation_count = len(conversation_history) // 2
            
            therapist_response = therapist_service.generate_response(
                conversation_history,
                emotion,
                transcription,
                is_premium
            )
            print(f"✅ Réponse générée: {therapist_response[:100]}...")
            
            conversation_history.append({
                'role': 'assistant',
                'content': therapist_response,
                'timestamp': datetime.now().isoformat()
            })
            
            session.conversation_history = conversation_history
            session.transcription = transcription
            session.emotion_detected = emotion
            session.confidence = confidence
            session.danger_level = danger_analysis['danger_score']
            db.session.commit()
            
            # 9. QUESTIONS
            questions = therapist_service.generate_questions(emotion, conversation_count, is_premium)
            
            # 10. NETTOYER
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"✅ Fichier temporaire supprimé")
            
            print("\n✅ SUCCÈS - Réponse envoyée\n")
            
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
            print(f"\n❌ EXCEPTION DANS process_voice:")
            print(f"   Type: {type(e).__name__}")
            print(f"   Message: {str(e)}")
            traceback.print_exc()
            print("\n")
            
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            
            return jsonify({'error': str(e), 'type': type(e).__name__}), 500
    
    @app.route('/api/chat/end-session', methods=['POST'])
    def end_session():
        """Termine session + génère plan traitement"""
        
        try:
            data = request.json
            session_id = data.get('session_id')
            
            if not session_id:
                return jsonify({'error': 'session_id requis'}), 400
            
            session = db.session.get(Session, session_id)
            if not session:
                return jsonify({'error': 'Session introuvable'}), 404
            
            user = db.session.get(User, session.user_id)
            if not user:
                return jsonify({'error': 'Utilisateur introuvable'}), 404
            
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
        
        except Exception as e:
            print(f"❌ ERREUR dans end_session: {e}")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
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
