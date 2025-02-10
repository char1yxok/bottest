import time
from utils.api_client import BitgetClient
from config import API_KEY, SECRET_KEY, PASSPHRASE, SYMBOL

class RiskManager:
    def __init__(self):
        self.client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)
    
    def auto_manage(self):
        while True:
            try:
                positions = self.client.get_positions()
                for pos in positions:
                    if pos['symbol'] != SYMBOL:
                        continue
                    
                    unrealized_pnl = float(pos['unrealizedPL'])
                    margin = float(pos['margin'])
                    
                    if margin == 0:
                        continue
                    
                    pnl_ratio = unrealized_pnl / margin
                    
                    if pnl_ratio >= 0.05:
                        print(f"Taking profit: {pos['positionId']}")
                        self.client.close_position(pos)
                    elif pnl_ratio <= -0.03:
                        print(f"Stopping loss: {pos['positionId']}")
                        self.client.close_position(pos)
                
                time.sleep(60)
            
            except Exception as e:
                print(f"Risk management error: {e}")
                time.sleep(30)