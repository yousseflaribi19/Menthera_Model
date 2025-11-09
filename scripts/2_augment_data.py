import os
import librosa
import numpy as np
import soundfile as sf
from glob import glob
from tqdm import tqdm

# ============================================================================
# FONCTIONS UTILITAIRES (copiées directement)
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

# ============================================================================
# CLASSE D'AUGMENTATION
# ============================================================================

class DataAugmenter:
    def __init__(self):
        self.input_dir = 'data/final_dataset'
        self.output_dir = 'data/augmented'
        self.emotions = ['tristesse', 'colere', 'peur', 'anxiete', 'neutre']
        
        for emotion in self.emotions:
            os.makedirs(f'{self.output_dir}/{emotion}', exist_ok=True)
    
    def add_noise(self, audio, noise_factor=0.005):
        """Ajoute du bruit blanc"""
        noise = np.random.randn(len(audio))
        return audio + noise_factor * noise
    
    def time_stretch(self, audio, rate):
        """Change la vitesse"""
        return librosa.effects.time_stretch(audio, rate=rate)
    
    def pitch_shift(self, audio, sr, n_steps):
        """Change la hauteur"""
        return librosa.effects.pitch_shift(audio, sr=sr, n_steps=n_steps)
    
    def augment_file(self, file_path):
        """Augmente un fichier (crée 5 versions)"""
        try:
            # Charger
            audio, sr = librosa.load(file_path, sr=22050)
            
            # Nom de base
            base_name = os.path.basename(file_path).replace('.wav', '')
            emotion = os.path.basename(os.path.dirname(file_path))
            
            # 5 versions augmentées
            versions = [
                ('original', audio),
                ('noise', self.add_noise(audio)),
                ('slow', self.time_stretch(audio, 0.9)),
                ('fast', self.time_stretch(audio, 1.1)),
                ('pitch_up', self.pitch_shift(audio, sr, 2)),
            ]
            
            # Sauvegarder
            for name, aug_audio in versions:
                output_file = f'{self.output_dir}/{emotion}/{base_name}_{name}.wav'
                sf.write(output_file, aug_audio, sr)
        
        except Exception as e:
            print(f"    Erreur: {e}")
    
    def run(self):
        """Augmente tout le dataset"""
        print("\n" + "="*70)
        print("AUGMENTATION DES DONNÉES")
        print("="*70)
        
        # Vérifier que les données sont organisées
        if not os.path.exists(self.input_dir):
            print("\n Dataset pas encore organisé!")
            print(" Lance d'abord: python scripts/1_organize_ravdess.py\n")
            return
        
        stats_before = count_files(self.input_dir)
        total_before = print_stats(stats_before, "Avant augmentation")
        
        if total_before == 0:
            print(" Aucun fichier à augmenter!")
            return
        
        print(" Augmentation en cours (×5)...\n")
        
        for emotion in self.emotions:
            files = glob(f'{self.input_dir}/{emotion}/*.wav')
            
            if len(files) == 0:
                continue
            
            print(f"\n{emotion}: {len(files)} fichiers")
            
            for file in tqdm(files, desc=f"  {emotion}"):
                self.augment_file(file)
        
        stats_after = count_files(self.output_dir)
        total_after = print_stats(stats_after, "Après augmentation")
        
        print(f" Augmentation: {total_before} → {total_after} fichiers")
        print(f" Facteur: ×{total_after // total_before}")
        print("\n Prochaine étape: python scripts/3_train_model.py\n")

if __name__ == "__main__":
    augmenter = DataAugmenter()
    augmenter.run()
