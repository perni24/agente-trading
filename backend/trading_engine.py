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
        # Salva nella cartella sessions
        self.status_file = os.path.join('sessions', f'status_{self.params.bot_id}.json')
        
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
            'close': self.dataclose[0],
            # Qui potremo aggiungere indicatori, volumi, etc.
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
    datapath = os.path.join(basedir, 'data', data_file)
    
    try:
        if not os.path.exists(datapath):
            raise FileNotFoundError(f"File non trovato: {datapath}")
            
        data = bt.feeds.GenericCSVData(
            dataname=datapath,
            fromdate=datetime.datetime(2023, 1, 1),
            todate=datetime.datetime(2023, 12, 31),
            dtformat=('%Y-%m-%d'),
            datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=-1,
            headers=True
        )
        cerebro.adddata(data)
    except Exception as e:
        error_msg = f"ERRORE dati ({data_file}): {str(e)}"
        print(error_msg)
        with open(os.path.join('sessions', f'status_{bot_id}.json'), 'w') as f:
            json.dump({'bot_id': bot_id, 'status': 'Errore dati', 'error': error_msg}, f)
        return

    try:
        cerebro.broker.setcash(10000.0)
        print(f'[{bot_id}] Avvio su {data_file}')
        cerebro.run()
    except Exception as e:
        error_msg = f"ERRORE backtest: {str(e)}"
        print(error_msg)
        with open(os.path.join('sessions', f'status_{bot_id}.json'), 'w') as f:
            json.dump({'bot_id': bot_id, 'status': 'Errore backtest', 'error': error_msg}, f)

    # *** DEBUG LOOP ***
    import time
    status_file = os.path.join('sessions', f'status_{bot_id}.json')
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