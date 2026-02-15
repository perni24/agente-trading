# Agente di Trading AI - Documentazione Tecnica

## Visione d'Insieme
Questa applicazione è una piattaforma di trading algoritmico che integra l'intelligenza artificiale (**LightGBM**) con un motore di esecuzione e backtesting (**Backtrader**), il tutto gestito tramite una dashboard web intuitiva in **Flask**.

---

## 🏗️ Architettura del Sistema

L'applicazione è suddivisa in tre livelli principali:

### 1. Gestione Dati (`backend/download_data.py`)
*   **Funzionalità:** Permette di scaricare dati storici reali da Yahoo Finance.
*   **Punti Cruciali:**
    *   Supporta vari asset (Forex, Crypto, Azioni).
    *   Gestisce diversi timeframe (15m, 1h, 1d).
    *   Formatta i dati automaticamente per renderli compatibili con il motore di trading e il modello IA.

### 2. Intelligenza Artificiale (`backend/train_model.py` & `backend/ai_agent.py`)
*   **Modello:** Utilizza **LightGBM Classifier**, un algoritmo di Gradient Boosting estremamente veloce ed efficiente su dati tabulari.
*   **Feature Engineering:** Il sistema calcola automaticamente indicatori tecnici come **RSI**, **EMA (20/50)** e **MACD** per dare "contesto" all'IA.
*   **Inference:** L'agente IA carica il modello addestrato e fornisce segnali di `BUY`, `SELL` o `HOLD` con un punteggio di confidenza (0.0 - 1.0).

### 3. Motore di Esecuzione (`backend/trading_engine.py`)
*   **Core:** Basato su **Backtrader**.
*   **Integrazione:** Riceve i dati candela per candela e interroga l'agente IA prima di decidere se aprire o chiudere una posizione.
*   **Multi-Bot:** Progettato per essere eseguito in processi separati, permettendo il monitoraggio di più strategie o asset contemporaneamente.

---

## 🖥️ Interfaccia di Controllo (`run.py` & `backend/app.py`)
*   **Dashboard Web:** Una UI che permette di:
    *   Creare e avviare nuovi bot di trading.
    *   Scegliere dinamicamente il dataset CSV da utilizzare.
    *   Monitorare in tempo reale il valore del portafoglio, la posizione attuale e i log delle operazioni.
*   **Gestione Sessioni:** Pulizia automatica delle sessioni e monitoraggio dei processi attivi.

---

## 🚀 Flusso di Lavoro Tipico

1.  **Download:** Scarica i dati desiderati (es. EUR/USD a 15 minuti).
    ```powershell
    python backend/download_data.py --ticker EURUSD=X --interval 15m --start 2026-01-01 --end 2026-02-15
    ```
2.  **Training:** Addestra l'IA su quei dati per creare il "cervello" del bot.
    ```powershell
    python backend/train_model.py --data backend/data/EURUSD_X.csv --name trading_model.pkl
    ```
3.  **Esecuzione:** Avvia la dashboard e lancia il bot.
    ```powershell
    python run.py
    ```

---

## ⚠️ Punti Cruciali e Sicurezza
*   **Frequenza Dati:** Per il trading intraday (15m), Yahoo Finance limita lo storico a 60 giorni.
*   **Confidenza Modello:** Il bot agisce solo quando la probabilità stimata dall'IA supera una certa soglia (es. > 0.6 per l'acquisto).
*   **Isolamento:** Ogni bot opera nel suo spazio di memoria e scrive il proprio file di stato unico, garantendo che le strategie non interferiscano tra loro.

---

## 🛠️ Sviluppi Futuri
*   Integrazione di **Take Profit** e **Stop Loss** dinamici gestiti dall'IA.
*   Supporto per il **Live Trading** tramite API di broker (OANDA, Binance, IB).
*   Aggiunta di feature basate sulla **Sentiment Analysis** (news di mercato).
