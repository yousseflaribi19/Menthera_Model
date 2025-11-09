# app/ml/predictor.py
import numpy as np
import tensorflow as tf
from tensorflow import keras
import librosa
import joblib
import os

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
    
    def extract_features(self, audio_path):
        y, sr = librosa.load(audio_path, duration=self.duration, sr=self.sample_rate)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
        return np.mean(mfcc.T, axis=0)
    
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
