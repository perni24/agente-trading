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

    def notify_order(self, order):
        """Gestisce il ciclo di vita ordine e sblocca la strategia."""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            side = 'BUY' if order.isbuy() else 'SELL'
            self.log(
                f'ORDER COMPLETED {side} @ {order.executed.price:.5f} '
                f'(size: {order.executed.size})'
            )
        elif order.status == order.Canceled:
            self.log('ORDER CANCELED')
        elif order.status == order.Margin:
            self.log('ORDER MARGIN REJECTED')
        elif order.status == order.Rejected:
            self.log('ORDER REJECTED')

        # Qualunque stato finale deve liberare il lock ordine
        self.order = None
        self.write_status('Aggiornamento ordine')

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


def write_terminal_status(status_file, bot_id, status_label, event, error=None, extra_fields=None):
    """Scrive lo stato finale del bot in modo consistente."""
    payload = {}
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                payload = json.load(f)
        except Exception:
            payload = {}

    payload.update({
        'bot_id': bot_id,
        'timestamp': datetime.datetime.now().isoformat(),
        'status': status_label,
        'event': event
    })
    if error:
        payload['error'] = error
    if extra_fields:
        payload.update(extra_fields)
    with open(status_file, 'w') as f:
        json.dump(payload, f, indent=4)


def run_engine(bot_id, symbol, data_file, mode='backtest'):
    """
    Configura ed esegue il motore per un bot specifico.
    mode=backtest: termina al termine del dataset
    mode=live: resta attivo finche' il feed live produce dati
    """
    cerebro = bt.Cerebro()
    cerebro.addstrategy(AgentStrategy, bot_id=bot_id)

    # --- SORGENTE DATI ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    sessions_dir = os.path.join(basedir, 'sessions')
    os.makedirs(sessions_dir, exist_ok=True)
    datapath = os.path.join(basedir, 'data', data_file)
    status_file = os.path.join(sessions_dir, f'status_{bot_id}.json')
    
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
        write_terminal_status(
            status_file=status_file,
            bot_id=bot_id,
            status_label='Errore dati',
            event='Errore caricamento dati',
            error=error_msg
        )
        return

    try:
        initial_capital = 10000.0
        cerebro.broker.setcash(initial_capital)
        print(f'[{bot_id}] Avvio mode={mode} su {data_file}')
        cerebro.run()
    except Exception as e:
        error_msg = f"ERRORE esecuzione: {str(e)}"
        print(error_msg)
        write_terminal_status(
            status_file=status_file,
            bot_id=bot_id,
            status_label='Errore esecuzione',
            event='Errore run',
            error=error_msg
        )
        return

    if mode == 'backtest':
        final_value = round(cerebro.broker.getvalue(), 2)
        final_pnl = round(final_value - initial_capital, 2)
        write_terminal_status(
            status_file=status_file,
            bot_id=bot_id,
            status_label='Completato',
            event='Backtest terminato',
            extra_fields={
                'initial_capital': initial_capital,
                'final_portfolio_value': final_value,
                'final_pnl': final_pnl
            }
        )
    else:
        # In live reale il processo resta attivo durante cerebro.run().
        # Se arriviamo qui, il feed live si e' chiuso o la run e' terminata.
        final_value = round(cerebro.broker.getvalue(), 2)
        final_pnl = round(final_value - initial_capital, 2)
        write_terminal_status(
            status_file=status_file,
            bot_id=bot_id,
            status_label='Terminato',
            event='Feed live terminato',
            extra_fields={
                'initial_capital': initial_capital,
                'final_portfolio_value': final_value,
                'final_pnl': final_pnl
            }
        )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backtrader Bot Instance')
    parser.add_argument('--bot_id', type=str, required=True, help='ID univoco del bot')
    parser.add_argument('--symbol', type=str, default='EURUSD', help='Simbolo')
    parser.add_argument('--data_file', type=str, default='dati_esempio.csv', help='File CSV in backend/data/')
    parser.add_argument('--mode', type=str, choices=['backtest', 'live'], default='backtest', help='Modalita esecuzione')
    
    args = parser.parse_args()
    run_engine(args.bot_id, args.symbol, args.data_file, args.mode)
