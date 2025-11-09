import os

class Config:
    """Configuration de l'application"""
    
    # Serveur
    HOST = '0.0.0.0'
    PORT = 5005
    DEBUG = True
    
    # Chemins
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_WEIGHTS = os.path.join(BASE_DIR, 'models', 'emotion_classifier') 
    SCALER_PATH = os.path.join(BASE_DIR, 'models', 'scaler.pkl')
    LABEL_ENCODER_PATH = os.path.join(BASE_DIR, 'models', 'label_encoder.pkl')
    
    # Paramètres audio
    SAMPLE_RATE = 22050
    DURATION = 30  # secondes
    N_MFCC = 40
    
    # Émotions
    EMOTIONS = ['tristesse', 'colere', 'peur', 'anxiete', 'neutre']