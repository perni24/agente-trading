# Documentazione: backend/app.py

Il file `app.py` funge da server centrale dell'applicazione, basato sul framework **Flask**. Gestisce le interazioni tra l'interfaccia utente (Dashboard) e il motore di trading (Backtrader).

## Funzioni Principali

### 1. `cleanup_sessions()`
- **Scopo**: Pulizia iniziale dei file temporanei.
- **Logica**: All'avvio del server, cerca tutti i file `.json` nella cartella `backend/sessions/` e li rimuove. Questo assicura che non ci siano residui di sessioni precedenti o bot terminati in modo anomalo.

### 2. `home()`
- **Route**: `@app.route('/')`
- **Scopo**: Caricamento dell'interfaccia principale.
- **Logica**: Restituisce il template HTML `index.html` che costituisce la dashboard dell'utente.

### 3. `list_datasets()`
- **Route**: `@app.route('/list_datasets')` (GET)
- **Scopo**: Elencare i dati di trading disponibili.
- **Logica**: Scansiona la cartella `backend/data/` e restituisce un elenco di tutti i file `.csv`. Questi vengono poi mostrati nel menu a tendina della dashboard.

### 4. `start_bot()`
- **Route**: `@app.route('/start_bot')` (POST)
- **Scopo**: Avviare una nuova istanza di trading.
- **Logica**:
    1. Riceve i parametri (ID bot, simbolo, dataset, modalità).
    2. Verifica se un bot con lo stesso ID è già attivo.
    3. Utilizza `subprocess.Popen` per lanciare `trading_engine.py` come processo indipendente.
    4. Memorizza il riferimento al processo nel dizionario globale `active_bots`.

### 5. `stop_bot()`
- **Route**: `@app.route('/stop_bot')` (POST)
- **Scopo**: Arrestare un bot in esecuzione.
- **Logica**:
    1. Recupera il processo dal dizionario `active_bots`.
    2. Tenta di terminare il processo in modo "gentile" (`terminate()`) e, se non risponde, forza l'arresto (`kill()`).
    3. Rimuove il file di stato JSON corrispondente per pulire la UI.

### 6. `get_status()`
- **Route**: `@app.route('/status')` (GET)
- **Scopo**: Monitoraggio in tempo reale dei bot.
- **Logica**:
    1. Itera su tutti i bot registrati in `active_bots`.
    2. Per ogni bot, controlla se il processo è ancora vivo (`process.poll()`).
    3. Legge il file `status_{bot_id}.json` prodotto dal `trading_engine.py` per recuperare metriche come valore del portafoglio, ultimi log e prezzi.
    4. Restituisce un oggetto JSON aggregato con lo stato di tutta la flotta.

## Gestione Processi
Il server non esegue il trading direttamente nel thread principale. Ogni bot è un processo Python separato, garantendo che un eventuale crash o un carico elevato di un bot non blocchi l'intera dashboard o gli altri agenti.
