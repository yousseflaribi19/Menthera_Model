import os
import shutil
from glob import glob
from tqdm import tqdm

def organize_ravdess():
    print("\n" + "="*70)
    print(" ORGANISATION DE RAVDESS PAR ÉMOTION")
    print("="*70 + "\n")
    
    # Dossiers
    input_dir = 'data/raw/ravdess'
    output_dir = 'data/final_dataset'
    
    # Map RAVDESS → Nos 5 émotions
    # Format nom fichier RAVDESS: 03-01-05-01-02-01-12.wav
    # Position 3 (index 2) = code émotion
    emotion_map = {
        '01': 'neutre',      # neutral
        '03': None,          # happy (on ignore)
        '04': 'tristesse',   # sad
        '05': 'colere',      # angry
        '06': 'peur',        # fearful
        '07': 'anxiete',     # disgust → anxiété
        '08': None,          # surprised (on ignore)
    }
    
    emotions = ['tristesse', 'colere', 'peur', 'anxiete', 'neutre']
    
    # Créer dossiers de sortie
    for emotion in emotions:
        os.makedirs(f'{output_dir}/{emotion}', exist_ok=True)
    
    # Trouver tous les fichiers WAV
    print(" Recherche des fichiers...")
    wav_files = glob(f'{input_dir}/**/*.wav', recursive=True)
    print(f" {len(wav_files)} fichiers WAV trouvés\n")
    
    # Organiser par émotion
    stats = {emotion: 0 for emotion in emotions}
    
    print(" Organisation en cours...\n")
    for file_path in tqdm(wav_files, desc="Traitement"):
        filename = os.path.basename(file_path)
        parts = filename.split('-')
        
        if len(parts) >= 3:
            emotion_code = parts[2]
            emotion = emotion_map.get(emotion_code)
            
            if emotion:  # Si c'est une émotion qu'on veut
                # Nom de destination
                dest_file = f'{output_dir}/{emotion}/{filename}'
                
                # Copier le fichier
                shutil.copy2(file_path, dest_file)
                stats[emotion] += 1
    
    # Afficher statistiques
    print("\n" + "="*70)
    print(" RÉSULTAT DE L'ORGANISATION")
    print("="*70)
    print(f"{'Émotion':<15} {'Nombre de fichiers':<20}")
    print("-" * 35)
    
    total = 0
    for emotion, count in stats.items():
        print(f"{emotion:<15} {count:<20}")
        total += count
    
    print("-" * 35)
    print(f"{'TOTAL':<15} {total:<20}")
    print("="*70 + "\n")
    
    print(" Organisation terminée!")
    print(f" Fichiers organisés dans: {output_dir}/")
    print("\n Prochaine étape: python scripts/2_augment_data.py\n")

if __name__ == "__main__":
    organize_ravdess()
