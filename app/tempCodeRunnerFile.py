    try:
        therapist_service = TherapistServiceAdvanced(use_api=True)
        print("Service thérapeutique avancé (hybride) initialisé")
    except Exception as e:
        print("ERREUR init modèle hybride :", e)
        therapist_service = TherapistServiceFree()
        print("Service thérapeutique basique initialisé")
