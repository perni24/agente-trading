import os
import sys

# Aggiunge la cartella 'backend' al path di sistema per permettere gli import corretti
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    print("--- Avvio Agente di Trading ---")
    print("Accedi alla dashboard su: http://127.0.0.1:5000")
    
    from backend.app import app
    # Esegue l'app Flask
    app.run(debug=True, port=5000)
