import random
import joblib
import os
import pandas as pd
import pandas_ta as ta
import numpy as np

class TradingAgent:
    """
    Agente di trading che utilizza un modello LightGBM per le decisioni.
    """
    def __init__(self, model_name="trading_model.pkl"):
        self.model_path = os.path.join('backend', 'models', model_name)
        self.features_path = os.path.join('backend', 'models', f"{model_name}_features.pkl")
        self.model = None
        self.feature_cols = None
        
        # Buffer per i dati storici necessari al calcolo degli indicatori
        self.history = pd.DataFrame()
        self.min_history = 60 # Numero minimo di candele per calcolare gli indicatori (es. EMA 50)
        
        self.load_model()

    def load_model(self):
        """Carica il modello e la lista delle feature."""
        if os.path.exists(self.model_path) and os.path.exists(self.features_path):
            try:
                self.model = joblib.load(self.model_path)
                self.feature_cols = joblib.load(self.features_path)
                print(f"Modello AI caricato: {self.model_path}")
            except Exception as e:
                print(f"Errore nel caricamento del modello: {e}")
        else:
            print("Modello AI non trovato. Verrà usata la logica random.")

    def get_decision(self, market_data):
        """
        Analizza i dati di mercato e restituisce una decisione basata su LightGBM.
        """
        # Aggiungi i nuovi dati alla history
        new_row = pd.DataFrame([market_data])
        self.history = pd.concat([self.history, new_row], ignore_index=True)
        
        # Mantieni solo il necessario
        if len(self.history) > 200:
            self.history = self.history.tail(200)

        # Se non abbiamo abbastanza dati o il modello non è caricato, usa logica di fallback
        if self.model is None or len(self.history) < self.min_history:
            return self._mock_decision("Inizializzazione o Fallback")

        try:
            # Calcolo feature
            df = self.history.copy()
            df.columns = [col.lower() for col in df.columns]
            
            # Calcoliamo gli stessi indicatori del training
            df['rsi'] = ta.rsi(df['close'], length=14)
            df['ema_20'] = ta.ema(df['close'], length=20)
            df['ema_50'] = ta.ema(df['close'], length=50)
            macd = ta.macd(df['close'])
            df = pd.concat([df, macd], axis=1)
            
            # Prendi l'ultima riga (stato attuale)
            current_features = df[self.feature_cols].tail(1)
            
            if current_features.isnull().values.any():
                 return self._mock_decision("Indicatori non pronti")

            # Predizione
            prob = self.model.predict_proba(current_features)[0][1] # Probabilità classe 1 (Up)
            
            confidence = float(prob)
            
            if prob > 0.6: # Soglia acquisto
                return 'BUY', {"reason": f"LightGBM confidence: {confidence:.2f}", "confidence": confidence}
            elif prob < 0.4: # Soglia vendita
                return 'SELL', {"reason": f"LightGBM confidence: {1-confidence:.2f}", "confidence": 1-confidence}
            else:
                return 'HOLD', {"reason": f"LightGBM neutral: {confidence:.2f}", "confidence": confidence}

        except Exception as e:
            print(f"Errore durante l'inference: {e}")
            return self._mock_decision(f"Errore: {str(e)}")

    def _mock_decision(self, reason):
        """Logica di fallback casuale."""
        actions = ['HOLD', 'BUY', 'SELL']
        weights = [0.9, 0.05, 0.05]
        decision = random.choices(actions, weights=weights, k=1)[0]
        return decision, {"reason": f"AI Mock ({reason})"}
