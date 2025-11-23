# app/services/speech_service.py
import speech_recognition as sr
import os
from pydub import AudioSegment
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechToTextService:
    """Service de conversion voix → texte"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def convert_to_wav(self, audio_path):
        """Convertit n'importe quel format en WAV avec une gestion d'erreurs améliorée"""
        try:
            # First, check if file exists with detailed information
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path} (cwd: {os.getcwd()})")
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            logger.info(f"Processing audio file: {audio_path} (size: {file_size} bytes)")
            
            if file_size == 0:
                raise ValueError(f"Audio file is empty: {audio_path}")
            
            # Si c'est déjà un WAV, vérifier s'il est valide
            if audio_path.lower().endswith('.wav'):
                # Vérifier si le fichier WAV est lisible
                try:
                    with sr.AudioFile(audio_path) as source:
                        # Juste un test de lecture
                        pass
                    logger.info(f"Valid WAV file, using as-is: {audio_path}")
                    return audio_path
                except Exception as e:
                    logger.warning(f"Fichier WAV invalide, reconversion nécessaire: {audio_path} - {e}")
                    # Continuer avec la conversion
            
            # Créer un chemin temporaire pour le fichier WAV
            wav_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
            
            # Charger l'audio avec pydub (supporte de nombreux formats)
            audio = AudioSegment.from_file(audio_path)
            
            # Exporter en WAV avec des paramètres spécifiques pour compatibilité
            audio = audio.set_frame_rate(16000).set_channels(1)  # Standard pour la reconnaissance vocale
            audio.export(wav_path, format='wav', parameters=["-ac", "1", "-ar", "16000"])
            
            logger.info(f"Conversion réussie: {audio_path} → {wav_path}")
            return wav_path
        
        except Exception as e:
            logger.error(f"Erreur de conversion avec pydub: {str(e)}")
            logger.error(f"Audio file details - exists: {os.path.exists(audio_path)}, size: {os.path.getsize(audio_path) if os.path.exists(audio_path) else 'N/A'}")
            # En cas d'erreur, essayer avec librosa comme fallback
            try:
                import librosa
                import soundfile as sf
                import numpy as np
                
                logger.info("Tentative de conversion avec librosa...")
                
                # Charger avec librosa
                y, sr = librosa.load(audio_path, sr=16000, mono=True)
                
                # Créer un chemin temporaire pour le fichier WAV
                wav_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
                
                # Sauvegarder en WAV avec des paramètres corrects
                sf.write(wav_path, y, sr, subtype='PCM_16')
                
                logger.info(f"Conversion librosa réussie: {audio_path} → {wav_path}")
                return wav_path
            except Exception as e2:
                error_msg = f"Impossible de convertir le fichier audio: {str(e)} | Librosa error: {str(e2)}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    def audio_to_text(self, audio_path, language='fr-FR'):
        """Convertit audio en texte"""
        try:
            wav_path = self.convert_to_wav(audio_path)
            
            with sr.AudioFile(wav_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)  # Integer instead of float
                audio_data = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(
                audio_data, 
                language=language
            )
            
            return {
                'success': True,
                'text': text,
                'confidence': 1.0
            }
        
        except sr.UnknownValueError:
            return {
                'success': False,
                'error': 'Audio incompréhensible',
                'text': None
            }
        
        except sr.RequestError as e:
            return {
                'success': False,
                'error': f'Erreur API: {str(e)}',
                'text': None
            }
        
        except Exception as e:
            logger.error(f"Erreur dans audio_to_text: {str(e)}")
            logger.error(f"Audio file details - exists: {os.path.exists(audio_path)}, size: {os.path.getsize(audio_path) if os.path.exists(audio_path) else 'N/A'}")
            return {
                'success': False,
                'error': str(e),
                'text': None
            }