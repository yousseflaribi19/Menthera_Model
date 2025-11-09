import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from glob import glob
import joblib
from tqdm import tqdm
import matplotlib.pyplot as plt

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def count_files(directory):
    """Compte les fichiers par émotion"""
    emotions = ['tristesse', 'colere', 'peur', 'anxiete', 'neutre']
    stats = {}
    
    for emotion in emotions:
        path = f'{directory}/{emotion}'
        if os.path.exists(path):
            count = len(glob(f'{path}/*.wav'))
            stats[emotion] = count
        else:
            stats[emotion] = 0
    
    return stats

def print_stats(stats, title="Statistiques"):
    """Affiche les statistiques formatées"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")
    print(f"{'Émotion':<15} {'Fichiers':<10}")
    print("-" * 25)
    
    total = 0
    for emotion, count in stats.items():
        print(f"{emotion:<15} {count:<10}")
        total += count
    
    print("-" * 25)
    print(f"{'TOTAL':<15} {total:<10}")
    print(f"{'='*70}\n")
    
    return total

def extract_features(audio_path, sr=22050):
    """Extrait les features MFCC (40 coefficients) - 30 SECONDES"""
    try:
        import librosa
        # ✅ MODIFIÉ : 30 secondes au lieu de 3
        y, sr = librosa.load(audio_path, duration=30, sr=sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        mfcc_mean = np.mean(mfcc.T, axis=0)
        return mfcc_mean
    except Exception as e:
        print(f"⚠️ Erreur {audio_path}: {e}")
        return None

# ============================================================================
# CLASSE D'ENTRAÎNEMENT
# ============================================================================

class ModelTrainer:
    def __init__(self):
        self.data_dir = 'data/augmented'
        self.models_dir = 'models'
        self.emotions = ['tristesse', 'colere', 'peur', 'anxiete', 'neutre']
        os.makedirs(self.models_dir, exist_ok=True)
    
    def prepare_data(self):
        """Prépare les données d'entraînement"""
        print("\n🔊 Extraction des features MFCC...")
        
        X, y = [], []
        
        for emotion in self.emotions:
            files = glob(f'{self.data_dir}/{emotion}/*.wav')
            
            if len(files) == 0:
                print(f"⚠️ Aucun fichier pour {emotion}")
                continue
            
            print(f"\n{emotion}: {len(files)} fichiers")
            
            for file in tqdm(files, desc=f"  {emotion}"):
                features = extract_features(file)
                if features is not None:
                    X.append(features)
                    y.append(emotion)
        
        print(f"\n✓ Features extraites: {len(X)} échantillons")
        return np.array(X), np.array(y)
    
    def build_model(self):
        """Construit le modèle neural"""
        model = keras.Sequential([
            keras.layers.Dense(256, activation='relu', input_shape=(40,)),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(128, activation='relu'),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(64, activation='relu'),
            keras.layers.Dense(5, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def plot_history(self, history):
        """Affiche les graphiques d'entraînement"""
        plt.figure(figsize=(12, 4))
        
        # Loss
        plt.subplot(1, 2, 1)
        plt.plot(history.history['loss'], label='Train')
        plt.plot(history.history['val_loss'], label='Validation')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.title('Loss')
        plt.grid(True)
        
        # Accuracy
        plt.subplot(1, 2, 2)
        plt.plot(history.history['accuracy'], label='Train')
        plt.plot(history.history['val_accuracy'], label='Validation')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        plt.title('Accuracy')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(f'{self.models_dir}/training_history.png', dpi=100)
        print(f"✓ Graphique: {self.models_dir}/training_history.png")
        plt.close()
    
    def train(self):
        """Entraîne le modèle complet"""
        print("\n" + "="*70)
        print(" ENTRAÎNEMENT DU MODÈLE")
        print("="*70)
        
        # Vérifier données
        if not os.path.exists(self.data_dir):
            print("\n⚠️ Données augmentées introuvables!")
            print("👉 Lance: python scripts/2_augment_data.py\n")
            return
        
        # Stats dataset
        stats = count_files(self.data_dir)
        total = print_stats(stats, "Dataset d'entraînement")
        
        if total == 0:
            print("⚠️ Aucun fichier à entraîner!")
            return
        
        # Préparer données
        X, y = self.prepare_data()
        
        if len(X) == 0:
            print("\n⚠️ Aucune feature extraite!")
            return
        
        # Encoder labels
        print("\n🏷️ Encodage des labels...")
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        print(f"Classes: {list(le.classes_)}")
        
        # Normaliser
        print("📊 Normalisation...")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded,
            test_size=0.2,
            random_state=42,
            stratify=y_encoded
        )
        
        print(f"\n✓ Train: {len(X_train)} | Test: {len(X_test)}")
        
        # Construire modèle
        print("\n🏗️  Construction du modèle...")
        model = self.build_model()
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]
        
        # Entraîner
        print("\n🎯 Entraînement (50 epochs max)...\n")
        history = model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=50,
            batch_size=32,
            callbacks=callbacks,
            verbose=1
        )
        
        # Évaluer
        print("\n📊 Évaluation finale...")
        loss, acc = model.evaluate(X_test, y_test, verbose=0)
        
        print("\n" + "="*70)
        print(" RÉSULTATS")
        print("="*70)
        print(f"Loss:     {loss:.4f}")
        print(f"Accuracy: {acc*100:.2f}%")
        print("="*70)
        
        # Sauvegarder
        print("\n💾 Sauvegarde des artefacts...")
        
        # ✅ UTILISER .weights.h5 (compatible Keras 3)
        model.save_weights(f'{self.models_dir}/emotion_classifier.weights.h5')
        joblib.dump(scaler, f'{self.models_dir}/scaler.pkl')
        joblib.dump(le, f'{self.models_dir}/label_encoder.pkl')
        
        print(f"✓ {self.models_dir}/emotion_classifier.weights.h5")
        print(f"✓ {self.models_dir}/scaler.pkl")
        print(f"✓ {self.models_dir}/label_encoder.pkl")
        
        # Graphiques
        self.plot_history(history)
        
        print("\n✅ Entraînement terminé!")
        print("👉 Prochaine étape: python scripts/4_test_model.py\n")
        
        return acc

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train()
