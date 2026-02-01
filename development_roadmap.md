# Roadmap di Sviluppo: Agente di Trading

Questo documento delinea le fasi di sviluppo del progetto, concentrandosi prima sull'infrastruttura fondamentale, poi sull'estensione e infine sull'integrazione dell'AI.

---

## Fase 1: Infrastruttura Base (Flask + Backtrader Singola Sessione)

**Obiettivo:** Creare un'applicazione web funzionante end-to-end che possa avviare, fermare e monitorare una singola istanza di Backtrader tramite un'interfaccia Flask.

### Task:

1.  **Backend (`backend/app.py`):**
    *   **Gestione del Processo Backtrader (Avvio e Arresto):**
        *   [x] **1.1: Aggiungere l'endpoint `POST /start_bot` in `app.py`.**
        *   [x] **1.2: Aggiungere l'endpoint `POST /stop_bot` in `app.py`.**
        *   [x] **1.3: Implementare l'avvio del processo Backtrader in `app.py` (`POST /start_bot`).**
        *   [x] **1.4: Implementare l'arresto del processo Backtrader in `app.py` (`POST /stop_bot`).**
        *   [x] **1.5: Aggiungere controlli di stato al bot in `start_bot` e `stop_bot`.**

    *   **Meccanismo di Comunicazione dello Stato (`status.json`):**
        *   [x] **1.6: Creare il file `status.json` (anche vuoto) e l'endpoint `GET /status` in `app.py`.**
        *   [x] **1.7: Modificare `trading_engine.py` per scrivere lo stato su `status.json`.**
        *   [x] **1.8: Migliorare l'endpoint `GET /status` per includere lo stato del processo e le informazioni da `status.json`.**

2.  **Backtrader (`backend/trading_engine.py`):**
    *   [x] Mantenere la strategia di esempio semplice.
    *   [x] Modificare la strategia per scrivere periodicamente il suo stato (valore del portafoglio, posizione attuale, log eventi) nel file `status.json`.

3.  **Frontend (UI Base - `backend/templates/index.html` e `backend/static/js/main.js`):**
    *   [x] Aggiornare `index.html` con una dashboard di base.
    *   [x] Creare un file JavaScript (`main.js`) per gestire eventi e polling periodico.

---

## Fase 2: Estensione a N Sessioni (Backtrader Multi-Valuta)

**Obiettivo:** Trasformare il sistema da "Single-Bot" a "Multi-Bot", permettendo la gestione parallela di diverse istanze di trading (es. su diversi asset o strategie).

### Task:

1.  **Trading Engine (`backend/trading_engine.py`):**
    *   [x] **2.1: Supporto Argomenti CLI (Identità del Bot).**
    *   [x] **2.2: Isolamento dello Stato.**
2.  **Backend (`backend/app.py`):**
    *   [x] **2.3: Gestione Processi Multipli.**
    *   [x] **2.4: Aggiornamento Endpoint `/start_bot`.**
    *   [x] **2.5: Aggiornamento Endpoint `/stop_bot`.**
    *   [x] **2.6: Aggiornamento Endpoint `/status`.**
3.  **Frontend (`index.html` e `main.js`):**
    *   [x] **2.7: UI Creazione Bot.**
        *   [x] **2.8: Rendering Dinamico della Dashboard.**
            *   Rimuovere i controlli statici esistenti.
            *   In `main.js`, aggiornare la funzione di polling per ricevere la lista dei bot.
            *   Generare dinamicamente l'HTML (Card/Pannelli) per ogni bot attivo, ognuno con il suo pulsante "Stop" e i suoi dati.
    
    ---
    
    ## Fase 2.5: Consolidamento e Gestione Dati
    
    **Obiettivo:** Rendere il sistema flessibile permettendo la selezione di diversi dataset per ogni bot e migliorando la visualizzazione delle operazioni.
    
    ### Task:
    
    1.  **Backend - Gestione Dataset:**
        *   [x] **2.5.1: Struttura Dati.**
            *   Creare la cartella `backend/data` e spostare lì `dati_esempio.csv`.
            *   Creare un endpoint `GET /list_datasets` che restituisce la lista dei file CSV presenti in quella cartella.
        *   [x] **2.5.2: Aggiornamento Engine e Start.**
            *   Aggiornare `trading_engine.py` per accettare un nuovo argomento `--data_file`.
            *   Aggiornare l'endpoint `/start_bot` per ricevere `data_file` dal frontend e passarlo al sottoprocesso.
    
    2.  **Frontend - Selezione e Log:**
        *   [x] **2.5.3: Selezione Dataset.**
            *   Nel form di creazione bot, sostituire l'input manuale del "Simbolo" (o aggiungerne uno nuovo) con un menu a tendina `<select>` che si popola chiamando `/list_datasets`.
        *   [x] **2.5.4: Visualizzazione Log.**
            *   Modificare `AgentStrategy` per salvare gli ultimi 10 log nel `status.json` (invece di solo l'ultimo evento).
            *   Aggiornare la Card del bot in `main.js` per mostrare una piccola finestra di log scrollabile.
    
    ---
        ## Fase 3: Integrazione AI

**Obiettivo:** Sostituire la logica decisionale della strategia Backtrader con l'agente AI, rendendo il bot intelligente.

### Task:

1.  **Backend (`backend/trading_engine.py`):**
    *   [ ] Modificare la classe `AgentStrategy` per preparare i dati di mercato.
    *   [ ] Implementare la logica per inviare i dati preparati all'agente AI (potrebbe essere una chiamata API a un modello locale o remoto, o l'integrazione di una libreria AI).
    *   [ ] Gestire la risposta dell'agente AI e tradurla in ordini di Backtrader.
    *   [ ] Aggiungere la possibilità di configurare l'agente AI (modello da usare, parametri).

2.  **Preparazione e Addestramento AI:**
    *   [ ] Sviluppare o selezionare il modello AI più adatto.
    *   [ ] Raccolta e preparazione dei dati di addestramento.
    *   [ ] Addestramento e ottimizzazione del modello AI.
    *   [ ] Implementazione dell'interfaccia per interagire con il modello AI.