# app/ml/predictor.py
import numpy as np
import tensorflow as tf
from tensorflow import keras
import librosa
import joblib
import os
import logging
from pydub import AudioSegment
import tempfile

# Set up logging
logger = logging.getLogger(__name__)

class EmotionPredictor:
    """Classe pour prédire les émotions"""
    
    def __init__(self):
        # Chemins relatifs
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.model_weights = os.path.join(base_dir, 'models', 'emotion_classifier.weights.h5')
        self.scaler_path = os.path.join(base_dir, 'models', 'scaler.pkl')
        self.label_encoder_path = os.path.join(base_dir, 'models', 'label_encoder.pkl')
        
        self.duration = 30
        self.sample_rate = 22050
        self.n_mfcc = 40
        
        # Charger modèle
        self.model = keras.Sequential([
            keras.layers.Dense(256, activation='relu', input_shape=(40,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dense(5, activation='softmax')
        ])
        self.model.load_weights(self.model_weights)
        
        self.scaler = joblib.load(self.scaler_path)
        self.le = joblib.load(self.label_encoder_path)
        
        print("✅ Modèle chargé")
    
    def _ensure_proper_wav_format(self, audio_path):
        """Ensure the audio file is in proper WAV format for librosa"""
        try:
            # First, check if file exists with detailed information
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path} (cwd: {os.getcwd()})")
            
            # Check file size
            file_size = os.path.getsize(audio_path)
            logger.info(f"Processing audio file: {audio_path} (size: {file_size} bytes)")
            
            if file_size == 0:
                raise ValueError(f"Audio file is empty: {audio_path}")
            
            # If it's already a WAV file, try to load it directly
            if audio_path.lower().endswith('.wav'):
                try:
                    # Try to load it directly
                    y, sr = librosa.load(audio_path, duration=1, sr=None)  # Short test load
                    logger.info(f"Direct WAV load successful: {audio_path}")
                    return audio_path
                except Exception as e:
                    logger.warning(f"Direct WAV load failed, will convert: {e}")
            
            # Convert to proper WAV format using pydub
            logger.info(f"Converting {audio_path} to WAV format...")
            audio = AudioSegment.from_file(audio_path)
            # Export with proper parameters for librosa
            audio = audio.set_frame_rate(self.sample_rate).set_channels(1)
            
            # Create temporary file
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav.close()
            
            audio.export(temp_wav.name, format='wav', parameters=["-ac", "1", "-ar", str(self.sample_rate)])
            logger.info(f"Conversion successful: {audio_path} → {temp_wav.name}")
            return temp_wav.name
        except Exception as e:
            logger.error(f"Failed to convert audio to WAV: {e}")
            logger.error(f"Audio file details - exists: {os.path.exists(audio_path)}, size: {os.path.getsize(audio_path) if os.path.exists(audio_path) else 'N/A'}")
            raise Exception(f"Could not process audio file: {str(e)}")
    
    def extract_features(self, audio_path):
        """Extract MFCC features from audio file"""
        temp_file_created = False
        processed_audio_path = None
        
        try:
            # Ensure proper WAV format
            processed_audio_path = self._ensure_proper_wav_format(audio_path)
            temp_file_created = (processed_audio_path != audio_path)
            
            # Load audio with librosa
            logger.info(f"Loading audio for feature extraction: {processed_audio_path}")
            y, sr = librosa.load(processed_audio_path, duration=self.duration, sr=self.sample_rate)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
            
            return np.mean(mfcc.T, axis=0)
        except Exception as e:
            logger.error(f"Error in extract_features: {e}")
            raise e
        finally:
            # Clean up temporary file if it was created
            if temp_file_created and processed_audio_path and os.path.exists(processed_audio_path):
                try:
                    os.unlink(processed_audio_path)
                    logger.info(f"Temporary file cleaned up: {processed_audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {processed_audio_path}: {e}")
    
    def predict(self, audio_path):
        features = self.extract_features(audio_path).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        predictions = self.model.predict(features_scaled, verbose=0)
        
        emotion_idx = np.argmax(predictions[0])
        emotion = self.le.classes_[emotion_idx]
        confidence = float(predictions[0][emotion_idx])
        
        probabilities = {
            self.le.classes_[i]: float(predictions[0][i])
            for i in range(len(self.le.classes_))
        }
        
        return {
            'emotion': emotion,
            'confidence': confidence,
            'probabilities': probabilities
        }