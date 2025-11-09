# app/services/speech_service.py
import speech_recognition as sr
import os
from pydub import AudioSegment

class SpeechToTextService:
    """Service de conversion voix → texte"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def convert_to_wav(self, audio_path):
        """Convertit n'importe quel format en WAV"""
        if audio_path.endswith('.wav'):
            return audio_path
        
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
        audio.export(wav_path, format='wav')
        
        return wav_path
    
    def audio_to_text(self, audio_path, language='fr-FR'):
        """Convertit audio en texte"""
        try:
            wav_path = self.convert_to_wav(audio_path)
            
            with sr.AudioFile(wav_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
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
