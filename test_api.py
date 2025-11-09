import requests
import json
from glob import glob
import random

def test_api():
    """Teste l'API avec des fichiers audio réels"""
    
    print("\n" + "="*70)
    print(" TEST DE L'API")
    print("="*70 + "\n")
    
    # URL de l'API
    url = 'http://localhost:5005/analyze-audio'
    
    # Trouver des fichiers de test
    test_files = glob('data/augmented/tristesse/*.wav')[:3]
    test_files += glob('data/augmented/colere/*.wav')[:3]
    test_files += glob('data/augmented/peur/*.wav')[:3]
    
    if len(test_files) == 0:
        print(" Aucun fichier de test trouvé!")
        print(" Lance d'abord: python scripts/2_augment_data.py\n")
        return
    
    # Tester quelques fichiers
    random.shuffle(test_files)
    
    for i, file_path in enumerate(test_files[:5], 1):
        print(f"\n{i}. Test de: {file_path}")
        
        try:
            response = requests.post(
                url,
                json={'audioPath': file_path},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['success']:
                    print(f"    Émotion: {result['emotion']}")
                    print(f"    Confiance: {result['confidence']:.1%}")
                    print(f"    {result['responseText']}")
                else:
                    print(f"    Erreur: {result.get('error')}")
            else:
                print(f"    Status: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            print("    API non accessible!")
            print("   Lance d'abord: python app/app.py")
            break
        
        except Exception as e:
            print(f"    Erreur: {e}")
    
    print("\n" + "="*70)
    print(" Tests terminés!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_api()
