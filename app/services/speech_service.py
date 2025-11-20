# app/services/speech_service.py
import speech_recognition as sr
import os
from pydub import AudioSegment
import tempfile

class SpeechToTextService:
    """Service de conversion voix → texte"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def convert_to_wav(self, audio_path):
        """Convertit n'importe quel format en WAV"""
        try:
            # Si c'est déjà un WAV, retourner le chemin
            if audio_path.lower().endswith('.wav'):
                return audio_path
            
            # Créer un chemin temporaire pour le fichier WAV
            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
            
            # Charger l'audio avec pydub (supporte de nombreux formats)
            audio = AudioSegment.from_file(audio_path)
            
            # Exporter en WAV
            audio.export(wav_path, format='wav')
            
            return wav_path
        
        except Exception as e:
            # En cas d'erreur, essayer avec librosa comme fallback
            try:
                import librosa
                import soundfile as sf
                import numpy as np
                
                # Charger avec librosa
                y, sr = librosa.load(audio_path, sr=None)
                
                # Créer un chemin temporaire pour le fichier WAV
                wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                
                # Sauvegarder en WAV
                sf.write(wav_path, y, sr)
                
                return wav_path
            except Exception as e2:
                raise Exception(f"Impossible de convertir le fichier audio: {str(e)} | {str(e2)}")
    
    def audio_to_text(self, audio_path, language='fr-FR'):
        """Convertit audio en texte"""
        try:
            wav_path = self.convert_to_wav(audio_path)
            
            with sr.AudioFile(wav_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
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
            return {
                'success': False,
                'error': str(e),
                'text': None
            }