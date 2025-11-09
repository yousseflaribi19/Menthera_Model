import os
import numpy as np
import librosa
from glob import glob

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
    """Extrait les features MFCC (40 coefficients)"""
    try:
        y, sr = librosa.load(audio_path, duration=3, sr=sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        mfcc_mean = np.mean(mfcc.T, axis=0)
        return mfcc_mean
    except Exception as e:
        print(f" Erreur {audio_path}: {e}")
        return None
