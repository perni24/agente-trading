import yfinance as yf
import pandas as pd
import os
import argparse
import sys

def download_ticker(ticker, start, end, interval="1d"):
    """
    Scarica i dati da Yahoo Finance e li salva in formato CSV compatibile.
    """
    print(f"--- Inizio Download ---")
    print(f"Ticker:   {ticker}")
    print(f"Periodo:  {start} -> {end}")
    print(f"Interval: {interval}")
    
    try:
        data = yf.download(ticker, start=start, end=end, interval=interval)
        
        if data.empty:
            print("\n!!! ERRORE: Nessun dato scaricato !!!")
            print("Possibili cause:")
            print("1. Il ticker potrebbe essere errato (es. usa 'EURUSD=X' per il Forex).")
            print("2. L'intervallo temporale richiesto non è disponibile per questo ticker.")
            print("3. Per intervalli intraday (15m, 1h), Yahoo Finance fornisce solo dati recenti (max 60 giorni).")
            return

        # Debug: Mostra le prime righe e le colonne
        print(f"\nDati scaricati con successo! Righe totali: {len(data)}")

        # Reset dell'indice per avere la data come colonna
        data = data.reset_index()
        
        # Gestione MultiIndex (comune nelle versioni recenti di yfinance)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] if col[1] == '' else col[0] for col in data.columns]

        # Assicuriamoci che le colonne siano Date, Open, High, Low, Close, Volume
        # Nota: Per i dati intraday la colonna si chiama 'Datetime' o 'Date'
        if 'Datetime' in data.columns:
            data = data.rename(columns={'Datetime': 'Date'})
        
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        data = data[required_cols]
        
        # Rimuovi informazioni sul fuso orario dalla colonna Date se presenti
        data['Date'] = pd.to_datetime(data['Date']).dt.tz_localize(None)
        
        # Formattazione per il CSV
        if interval in ['1d', '1wk', '1mo']:
            data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
        else:
            data['Date'] = data['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Creazione cartella se non esiste
        os.makedirs('backend/data', exist_ok=True)
        
        clean_ticker = ticker.replace('=', '_').replace('-', '_')
        output_path = f"backend/data/{clean_ticker}.csv"
        
        data.to_csv(output_path, index=False)
        
        print(f"File salvato in: {os.path.abspath(output_path)}")
        print(f"--- Download Completato ---")

    except Exception as e:
        print(f"\n!!! ERRORE INASPETTATO: {str(e)} !!!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download data from Yahoo Finance')
    parser.add_argument('--ticker', type=str, default='EURUSD=X', help='Ticker (es. BTC-USD, EURUSD=X)')
    parser.add_argument('--start', type=str, required=True, help='Data inizio (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='Data fine (YYYY-MM-DD)')
    parser.add_argument('--interval', type=str, default='1d', help='Interval (1d, 1h, 15m, 5m)')
    
    args = parser.parse_args()
    download_ticker(args.ticker, args.start, args.end, args.interval)
