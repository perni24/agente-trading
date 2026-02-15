from flask import Flask, render_template, jsonify, request
import webbrowser
import time
import json
import subprocess
import sys
import os

app = Flask(__name__)

# Dizionario per tenere traccia dei processi Backtrader attivi
# Struttura: { 'bot_id': subprocess.Popen_object }
active_bots = {}

def cleanup_sessions():
    sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')
    if os.path.exists(sessions_dir):
        for f in os.listdir(sessions_dir):
            if f.endswith('.json'):
                try:
                    os.remove(os.path.join(sessions_dir, f))
                except:
                    pass
    else:
        os.makedirs(sessions_dir, exist_ok=True)

cleanup_sessions()

@app.route('/')
def home():
    return render_template('index.html')

# Endpoint per elencare i dataset disponibili
@app.route('/list_datasets', methods=['GET'])
def list_datasets():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    try:
        if not os.path.exists(data_dir):
            return jsonify([]), 200
        files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        return jsonify(files), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint per avviare un bot di trading specifico
@app.route('/start_bot', methods=['POST'])
def start_bot():
    data = request.get_json()
    if not data or 'bot_id' not in data:
        return jsonify({'message': 'Parametro bot_id mancante.'}), 400
    
    bot_id = data['bot_id']
    symbol = data.get('symbol', 'EURUSD')
    data_file = data.get('data_file', 'dati_esempio.csv') # Default file
    mode = data.get('mode', 'backtest')

    if bot_id in active_bots:
        if active_bots[bot_id].poll() is None:
            return jsonify({'message': f'Il bot {bot_id} è già in esecuzione.'}), 409
        else:
            del active_bots[bot_id]

    try:
        # Costruzione comando con il nuovo parametro --data_file
        # Percorso assoluto del motore di trading
        engine_path = os.path.join(os.path.dirname(__file__), 'trading_engine.py')
        
        cmd = [
            sys.executable, engine_path, 
            '--bot_id', bot_id, 
            '--symbol', symbol,
            '--data_file', data_file,
            '--mode', mode
        ]
        
        # Avvia il processo senza bloccare lo stdout/stderr per vederli in console
        process = subprocess.Popen(
            cmd,
            cwd='.', 
            # Rimuoviamo PIPE per vedere i log direttamente nella console durante lo sviluppo
            stdout=None,
            stderr=None
        )
        
        # Un piccolo delay per vedere se crasha subito
        time.sleep(1)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            return jsonify({
                'message': f'Il bot {bot_id} è partito ma si è interrotto immediatamente.',
                'output': stdout.strip(),
                'error': stderr.strip()
            }), 500

        # Registra il bot attivo
        active_bots[bot_id] = process
        return jsonify({'message': f'Bot {bot_id} avviato con successo su {symbol} ({mode}).'}), 200
    except Exception as e:
        return jsonify({'message': f'Errore interno durante l\'avvio del bot {bot_id}: {str(e)}'}), 500

# Endpoint per fermare un bot specifico
@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    data = request.get_json()
    if not data or 'bot_id' not in data:
        return jsonify({'message': 'Parametro bot_id mancante.'}), 400

    bot_id = data['bot_id']
    
    if bot_id not in active_bots:
        return jsonify({'message': f'Il bot {bot_id} non è attivo.'}), 404

    process = active_bots[bot_id]
    
    try:
        # Verifica se è già terminato
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        
        # Rimuove dal dizionario in modo sicuro
        if bot_id in active_bots:
            del active_bots[bot_id]
        
        # Gestione cancellazione file con percorso assoluto sicuro
        sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')
        status_file = os.path.join(sessions_dir, f'status_{bot_id}.json')
        if os.path.exists(status_file):
            for i in range(3): # Tenta 3 volte
                try:
                    os.remove(status_file)
                    break
                except OSError:
                    time.sleep(0.5)
                except Exception:
                    pass 

        return jsonify({'message': f'Bot {bot_id} fermato con successo.'}), 200
    except Exception as e:
        return jsonify({'message': f'Errore durante l\'arresto del bot {bot_id}: {str(e)}'}), 500

# Endpoint per ottenere lo stato di tutti i bot
@app.route('/status', methods=['GET'])
def get_status():
    all_statuses = {}
    
    # Crea una copia delle chiavi per iterare
    current_bot_ids = list(active_bots.keys())
    
    if not current_bot_ids:
        return jsonify({}), 200

    for bot_id in current_bot_ids:
        # Usa .get() per evitare KeyError se il bot viene rimosso concurrentemente
        process = active_bots.get(bot_id)
        
        # Se il bot non esiste più nel dizionario, saltalo
        if not process:
            continue
            
        bot_data = {
            'bot_running': process.poll() is None,
            'pid': process.pid if process.poll() is None else None
        }

        # Tenta di leggere il file di stato specifico
        sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')
        status_file = os.path.join(sessions_dir, f'status_{bot_id}.json')
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    file_data = json.load(f)
                    bot_data.update(file_data)
            except Exception:
                bot_data['file_status'] = 'Errore lettura file stato'
        else:
            bot_data['file_status'] = 'File stato non ancora creato'
            
        all_statuses[bot_id] = bot_data

    return jsonify(all_statuses), 200

if __name__ == '__main__':
    time.sleep(1)
    # Apri il browser solo se non stiamo ricaricando (debug mode quirks)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)



