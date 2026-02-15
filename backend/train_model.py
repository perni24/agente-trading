import pandas as pd
import pandas_ta as ta
import lightgbm as lgb
import joblib
import os
import argparse

def prepare_data(df):
    """
    Calcola gli indicatori tecnici e prepara le feature per il modello.
    """
    # Assicurati che le colonne siano minuscole per pandas_ta
    df.columns = [col.lower() for col in df.columns]
    
    # Feature Engineering con pandas_ta
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['ema_20'] = ta.ema(df['close'], length=20)
    df['ema_50'] = ta.ema(df['close'], length=50)
    
    macd = ta.macd(df['close'])
    df = pd.concat([df, macd], axis=1)
    
    # Target: 1 se il prezzo di chiusura della candela SUCCESSIVA è superiore a quella attuale
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    
    # Rimuovi righe con valori NaN (dovuti agli indicatori e allo shift)
    df.dropna(inplace=True)
    
    return df

def train_model(data_path, model_name="trading_model.pkl"):
    """
    Addestra un modello LightGBM sui dati forniti.
    """
    if not os.path.exists(data_path):
        print(f"Errore: File {data_path} non trovato.")
        return

    print(f"Caricamento dati da {data_path}...")
    df = pd.read_csv(data_path)
    
    df = prepare_data(df)
    
    # Definizione delle feature
    feature_cols = ['rsi', 'ema_20', 'ema_50', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']
    X = df[feature_cols]
    y = df['target']
    
    # Split semplice (80% train, 20% test) - In produzione andrebbe usato un TimeSeriesSplit
    split = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    print("Addestramento modello LightGBM...")
    model = lgb.LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
        verbose=-1
    )
    
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)])
    
    # Salvataggio
    model_path = os.path.join('backend', 'models', model_name)
    joblib.dump(model, model_path)
    print(f"Modello salvato in: {model_path}")
    
    # Salva anche la lista delle feature per coerenza in fase di inference
    joblib.dump(feature_cols, os.path.join('backend', 'models', f"{model_name}_features.pkl"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train LightGBM Trading Model')
    parser.add_argument('--data', type=str, default='backend/data/dati_esempio.csv', help='Percorso file CSV')
    parser.add_argument('--name', type=str, default='trading_model.pkl', help='Nome del modello da salvare')
    
    args = parser.parse_args()
    train_model(args.data, args.name)
