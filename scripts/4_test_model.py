import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
import joblib
from glob import glob
import random

# FONCTIONS UTILITAIRES

def extract_features(audio_path, sr=22050):
    """Extrait les features MFCC (40 coefficients)"""
    try:
        import librosa
        y, sr = librosa.load(audio_path, duration=3, sr=sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        mfcc_mean = np.mean(mfcc.T, axis=0)
        return mfcc_mean
    except Exception as e:
        print(f" Erreur {audio_path}: {e}")
        return None

# CLASSE DE TEST

class ModelTester:
    def __init__(self):
        # Vérifier que le modèle existe
        if not os.path.exists('models/emotion_classifier.weights.h5'):
            print("\n Modèle non trouvé!")
            print(" Lance d'abord: python scripts/3_train_model.py\n")
            return
        
        # Charger modèle
        self.model = keras.Sequential([
            keras.layers.Dense(256, activation='relu', input_shape=(40,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dense(5, activation='softmax')
        ])
        self.model.load_weights('models/emotion_classifier.weights.h5')
        
        self.scaler = joblib.load('models/scaler.pkl')
        self.le = joblib.load('models/label_encoder.pkl')
        
        print(" Modèle chargé!")
    
    def predict(self, audio_path):
        """Prédit l'émotion d'un fichier audio"""
        features = extract_features(audio_path)
        if features is None:
            return None, 0.0, {}
        
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        predictions = self.model.predict(features_scaled, verbose=0)
        
        emotion_idx = np.argmax(predictions[0])
        emotion = self.le.classes_[emotion_idx]
        confidence = float(predictions[0][emotion_idx])
        
        # Toutes les probabilités
        probabilities = {
            self.le.classes_[i]: float(predictions[0][i])
            for i in range(len(self.le.classes_))
        }
        
        return emotion, confidence, probabilities
    
    def test_random_samples(self, num_samples=20):
        """Teste sur des échantillons aléatoires"""
        print("\n" + "="*70)
        print("TEST DU MODÈLE")
        print("="*70)
        
        data_dir = 'data/augmented'
        emotions = ['tristesse', 'colere', 'peur', 'anxiete', 'neutre']
        
        print(f"\nTest sur {num_samples} échantillons aléatoires...\n")
        
        correct = 0
        total = 0
        results_by_emotion = {e: {'correct': 0, 'total': 0} for e in emotions}
        
        for emotion in emotions:
            files = glob(f'{data_dir}/{emotion}/*.wav')
            
            if len(files) == 0:
                continue
            
            # Échantillons aléatoires
            samples = random.sample(files, min(num_samples // len(emotions), len(files)))
            
            for file in samples:
                predicted, confidence, probs = self.predict(file)
                
                if predicted:
                    total += 1
                    results_by_emotion[emotion]['total'] += 1
                    
                    if predicted == emotion:
                        correct += 1
                        results_by_emotion[emotion]['correct'] += 1
                        status = "✅"
                    else:
                        status = "❌"
                    
                    filename = os.path.basename(file)[:30]
                    print(f"{status} Vrai: {emotion:<10} | Prédit: {predicted:<10} | Conf: {confidence:.1%} | {filename}")
        
        # Résultats globaux
        accuracy = (correct / total * 100) if total > 0 else 0
        
        print("\n" + "="*70)
        print(f" RÉSULTATS GLOBAUX")
        print("="*70)
        print(f"Correct: {correct}/{total}")
        print(f"Précision: {accuracy:.1f}%")
        
        # Résultats par émotion
        print("\n" + "="*70)
        print(f" RÉSULTATS PAR ÉMOTION")
        print("="*70)
        
        for emotion in emotions:
            res = results_by_emotion[emotion]
            if res['total'] > 0:
                acc = (res['correct'] / res['total'] * 100)
                print(f"{emotion:<15} {res['correct']}/{res['total']} ({acc:.1f}%)")
        
        print("="*70 + "\n")
        
        print(" Tests terminés!")
        print("\n Prochaine étape: python app/app.py\n")

if __name__ == "__main__":
    tester = ModelTester()
    tester.test_random_samples(20)
