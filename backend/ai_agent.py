import random

class TradingAgent:
    """
    Classe base per l'agente di trading AI.
    Attualmente implementa una logica dummy per testare l'integrazione.
    """
    def __init__(self, strategy_name="random"):
        self.strategy_name = strategy_name

    def get_decision(self, market_data):
        """
        Analizza i dati di mercato e restituisce una decisione.
        
        Args:
            market_data (dict): Dizionario contenente i dati di mercato 
                                (es. prezzo attuale, storico, indicatori).
        
        Returns:
            str: 'BUY', 'SELL', o 'HOLD'
            dict: Metadati addizionali (es. confidence, reason)
        """
        # --- LOGICA TEMPORANEA (MOCK) ---
        # Qui in futuro ci sarà la chiamata al modello AI o API.
        
        # Esempio: decisione casuale pesata
        actions = ['HOLD', 'BUY', 'SELL']
        weights = [0.8, 0.1, 0.1] # 80% HOLD, 10% BUY, 10% SELL
        
        decision = random.choices(actions, weights=weights, k=1)[0]
        
        reason = f"Logica mock ({self.strategy_name}): decisione casuale."
        
        return decision, {"reason": reason}
