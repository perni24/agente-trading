# Roadmap Correttiva: Agente di Trading

Questa roadmap sostituisce il piano precedente ed e' focalizzata sui problemi reali emersi dall'analisi del codice.

---

## Priorita P0 (Blocchi Funzionali e Sicurezza)

**Obiettivo:** rendere il sistema corretto, fermabile e sicuro prima di qualsiasi nuova feature.

1. **Correggere il blocco della strategia dopo il primo ordine** (`backend/trading_engine.py`)
- [x] Implementare `notify_order` e azzerare `self.order` quando l'ordine e' `Completed`, `Canceled`, `Margin` o `Rejected`.
- [x] Evitare che `next()` resti permanentemente in `return` dopo il primo trade.
- [x] Aggiungere log espliciti sul ciclo ordine per debug.
  Implementato in `backend/trading_engine.py` con gestione stati ordine, reset lock ordine e aggiornamento stato sessione.

2. **Rimuovere il loop infinito post-backtest** (`backend/trading_engine.py`)
- [x] Eliminare il `while True` finale usato come debug.
- [x] Chiudere il processo in modo pulito al termine del backtest.
- [x] Scrivere stato finale una sola volta (`Completato` / `Errore`).
  Implementato con modalita `--mode backtest|live`, stati terminali espliciti e nessun keep-alive artificiale.

3. **Allineare i path dei file di sessione** (`backend/app.py`, `backend/trading_engine.py`)
- [ ] Usare path assoluti basati su `os.path.dirname(__file__)` sia in scrittura che in lettura.
- [ ] Uniformare il path `backend/sessions/status_<bot_id>.json` in tutti gli endpoint.

4. **Correggere gestione crash in avvio bot** (`backend/app.py`)
- [ ] Se si vogliono leggere output/errori, usare `stdout=subprocess.PIPE` e `stderr=subprocess.PIPE`.
- [ ] In alternativa, rimuovere `.strip()` su valori `None` e gestire messaggio fallback robusto.

5. **Bloccare path traversal su `bot_id` e `data_file`** (`backend/app.py`, `backend/trading_engine.py`)
- [ ] Validare `bot_id` con allowlist (es. `^[A-Za-z0-9_-]{1,64}$`).
- [ ] Verificare che `data_file` punti solo a file presenti in `backend/data` (niente `..`, niente path assoluti).
- [ ] Rifiutare input non validi con `400`.

6. **Eliminare XSS nella dashboard** (`backend/static/js/main.js`)
- [ ] Smettere di costruire card con `innerHTML` su dati non trusted.
- [ ] Usare `textContent` e creazione nodi DOM esplicita.
- [ ] Rimuovere `onclick` inline e usare `addEventListener`.

7. **Disattivare fallback random in produzione** (`backend/ai_agent.py`)
- [ ] Quando modello non pronto o feature non pronte, restituire solo `HOLD`.
- [ ] Rendere il comportamento configurabile via flag (`safe_mode=True` default).

---

## Priorita P1 (Robustezza Runtime)

**Obiettivo:** evitare stati inconsistenti e problemi in uso concorrente.

1. **Gestione concorrente di `active_bots`** (`backend/app.py`)
- [ ] Proteggere accesso con lock (`threading.Lock`) o serializzare modifiche.
- [ ] Rendere atomiche le operazioni start/stop/status.

2. **Pulizia automatica processi terminati** (`backend/app.py`)
- [ ] Durante `/status`, rimuovere bot con processo terminato.
- [ ] Esporre chiaramente `stopped_at` e motivo termine.

3. **Rilevamento timeframe corretto** (`backend/trading_engine.py`)
- [ ] Non hardcodare `compression=15` per tutti gli intraday.
- [ ] Inferire timeframe dal dataset o passarlo esplicitamente da UI/API.

4. **Path modello robusti e indipendenti dalla cwd** (`backend/ai_agent.py`, `backend/train_model.py`)
- [ ] Usare path assoluti basati sulla directory del file Python.
- [ ] Creare sempre `backend/models` prima di salvare.

5. **Coerenza API: rimuovere parametri inutilizzati** (`backend/app.py`, `backend/trading_engine.py`)
- [ ] Eliminare `symbol` se non serve, oppure usarlo realmente nel motore.

---

## Priorita P2 (Qualita, Osservabilita, Manutenzione)

**Obiettivo:** stabilizzare il progetto e ridurre regressioni future.

1. **Test automatici minimi**
- [ ] Unit test su validazione input (`bot_id`, `data_file`).
- [ ] Test integrazione su `/start_bot`, `/stop_bot`, `/status`.
- [ ] Test strategia: apertura/chiusura ordini multipli senza freeze.
- [ ] Test AI: assenza di `BUY/SELL` random in fallback sicuro.

2. **Configurazione runtime**
- [ ] Introdurre file/config env per soglie AI (`buy_threshold`, `sell_threshold`) e modalita debug.
- [ ] Disabilitare `debug=True` di default nei run path standard.

3. **Encoding e igiene codice**
- [ ] Uniformare file a UTF-8 senza caratteri corrotti.
- [ ] Rimuovere import inutilizzati (`numpy`, `sys` dove non necessari).

4. **Policy sessioni**
- [ ] Rivedere `cleanup_sessions()` per non cancellare sempre tutto all'avvio.
- [ ] Introdurre retention configurabile o cleanup selettivo.

5. **Dashboard - Risultato finale bot**
- [x] Mostrare in UI l'esito finale del bot a run terminata.
- [x] Mostrare `Valore Finale` e `PnL` nelle card quando `bot_running=false`.
- [x] Allineare backend/frontend sul path sessioni per visualizzare correttamente i dati finali.

---

## Criteri di Accettazione

- [ ] Il bot puo' eseguire piu' ordini consecutivi senza bloccarsi dopo il primo trade.
- [ ] Un backtest termina senza lasciare processi zombie.
- [ ] Dashboard mostra sempre stato corretto del bot (path sessioni coerenti).
- [ ] Input malevoli su `bot_id`/`data_file` vengono respinti.
- [ ] Nessun dato utente viene renderizzato con rischio XSS.
- [ ] In fallback AI, il sistema non apre posizioni casuali.
- [ ] Esiste una suite di test base che copre i flussi critici.

---

## Ordine Esecutivo Consigliato

1. P0.1 -> P0.4 (funzionalita core)
2. P0.5 -> P0.7 (sicurezza)
3. P1 completo (robustezza runtime)
4. P2 completo (qualita e mantenibilita)
