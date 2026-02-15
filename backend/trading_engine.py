import backtrader as bt
import datetime
import os
import json
import argparse
from ai_agent import TradingAgent

class AgentStrategy(bt.Strategy):
    """
    Questa è la strategia di trading.
    Riceve un bot_id e gestisce i log recenti.
    Usa TradingAgent per prendere decisioni.
    """
    params = (
        ('bot_id', 'default_bot'),
    )

    def log(self, txt, dt=None):
        '''Funzione di logging per questa strategia'''
        dt = dt or self.datas[0].datetime.date(0)
        msg = f'{dt.isoformat()} {txt}'
        print(f'[{self.params.bot_id}] {msg}')
        
        # Mantieni solo gli ultimi 10 log
        if not hasattr(self, 'recent_logs'):
            self.recent_logs = []
        self.recent_logs.append(msg)
        if len(self.recent_logs) > 10:
            self.recent_logs.pop(0)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.recent_logs = []
        
        # Assicurati che la cartella sessions esista
        sessions_dir = os.path.join(os.path.dirname(__file__), 'sessions')
        os.makedirs(sessions_dir, exist_ok=True)
        
        # Salva nella cartella sessions usando il percorso assoluto
        self.status_file = os.path.join(sessions_dir, f'status_{self.params.bot_id}.json')
        
        # Inizializza l'Agente AI
        self.agent = TradingAgent()
        
        self.log('Strategia Inizializzata')
        self.write_status('Inizializzazione')

    def write_status(self, event="Update"):
        """Scrive lo stato attuale e i log recenti su file"""
        status = {
            'bot_id': self.params.bot_id,
            'timestamp': datetime.datetime.now().isoformat(),
            'event': event,
            'recent_logs': self.recent_logs,
            'portfolio_value': round(self.broker.getvalue(), 2),
            'cash': round(self.broker.getcash(), 2),
            'position_size': self.position.size,
            'last_close': self.dataclose[0] if len(self.dataclose) > 0 else None,
            'status': 'In esecuzione'
        }
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=4)
        except Exception as e:
            print(f"Errore nella scrittura di {self.status_file}: {str(e)}")

    def next(self):
        """Logica chiamata per ogni candela"""
        self.write_status()

        if self.order:
            return

        # Prepara i dati per l'agente
        market_data = {
            'open': self.datas[0].open[0],
            'high': self.datas[0].high[0],
            'low': self.datas[0].low[0],
            'close': self.datas[0].close[0],
            'volume': self.datas[0].volume[0]
        }

        # Chiedi all'Agente cosa fare
        decision, info = self.agent.get_decision(market_data)

        if decision == 'BUY' and not self.position:
            self.log(f'BUY SIGNAL ({info.get("reason")}) - Price: {self.dataclose[0]}')
            self.order = self.buy()
            self.write_status(f'Acquisto: {info.get("reason")}')
            
        elif decision == 'SELL' and self.position:
            self.log(f'SELL SIGNAL ({info.get("reason")}) - Price: {self.dataclose[0]}')
            self.order = self.sell()
            self.write_status(f'Vendita: {info.get("reason")}')


def run_backtest(bot_id, symbol, data_file):
    """
    Configura ed esegue il backtest per un bot specifico.
    """
    cerebro = bt.Cerebro()
    cerebro.addstrategy(AgentStrategy, bot_id=bot_id)

    # --- SORGENTE DATI ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    sessions_dir = os.path.join(basedir, 'sessions')
    os.makedirs(sessions_dir, exist_ok=True)
    datapath = os.path.join(basedir, 'data', data_file)
    
    try:
        if not os.path.exists(datapath):
            raise FileNotFoundError(f"File non trovato: {datapath}")
            
        # Rileva se il file contiene orari (intraday) o solo date
        with open(datapath, 'r') as f:
            first_line = f.readlines()[1] # Salta header
            is_intraday = ' ' in first_line.split(',')[0]

        if is_intraday:
            dt_format = '%Y-%m-%d %H:%M:%S'
            tf = bt.TimeFrame.Minutes
            compression = 15 # Assumiamo 15m come da tua richiesta, potremmo renderlo dinamico
        else:
            dt_format = '%Y-%m-%d'
            tf = bt.TimeFrame.Days
            compression = 1

        data = bt.feeds.GenericCSVData(
            dataname=datapath,
            dtformat=(dt_format),
            datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=-1,
            headers=True,
            timeframe=tf,
            compression=compression
        )
        cerebro.adddata(data)
    except Exception as e:
        error_msg = f"ERRORE dati ({data_file}): {str(e)}"
        print(error_msg)
        with open(os.path.join(sessions_dir, f'status_{bot_id}.json'), 'w') as f:
            json.dump({'bot_id': bot_id, 'status': 'Errore dati', 'error': error_msg}, f)
        return

    try:
        cerebro.broker.setcash(10000.0)
        print(f'[{bot_id}] Avvio su {data_file}')
        cerebro.run()
    except Exception as e:
        error_msg = f"ERRORE backtest: {str(e)}"
        print(error_msg)
        with open(os.path.join(sessions_dir, f'status_{bot_id}.json'), 'w') as f:
            json.dump({'bot_id': bot_id, 'status': 'Errore backtest', 'error': error_msg}, f)

    # *** DEBUG LOOP ***
    import time
    status_file = os.path.join(sessions_dir, f'status_{bot_id}.json')
    try:
        while True:
            try:
                if os.path.exists(status_file):
                    with open(status_file, 'r') as f:
                        status = json.load(f)
                else:
                    status = {'bot_id': bot_id}
                
                status['status'] = 'Completato (Idle)'
                status['last_update'] = datetime.datetime.now().isoformat()
                
                with open(status_file, 'w') as f:
                    json.dump(status, f, indent=4)
            except:
                pass
            time.sleep(5) 
    except KeyboardInterrupt:
        print(f"[{bot_id}] Interrotto.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backtrader Bot Instance')
    parser.add_argument('--bot_id', type=str, required=True, help='ID univoco del bot')
    parser.add_argument('--symbol', type=str, default='EURUSD', help='Simbolo')
    parser.add_argument('--data_file', type=str, default='dati_esempio.csv', help='File CSV in backend/data/')
    
    args = parser.parse_args()
    run_backtest(args.bot_id, args.symbol, args.data_file)