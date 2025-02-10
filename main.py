from utils.api_client import BitgetClient
from strategies.technical import calculate_indicators
from strategies.ai_strategy import AITrader
from strategies.risk_management import RiskManager
from config import API_KEY, SECRET_KEY, PASSPHRASE, SYMBOL, TIMEFRAME, SIZE
import pandas as pd
import time
import threading

client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)
ai_trader = AITrader()
risk_manager = RiskManager()

def fetch_data():
    candles = client.get_candles(SYMBOL, TIMEFRAME)
    return pd.DataFrame([{
        'timestamp': candle[0],
        'open': float(candle[1]),
        'high': float(candle[2]),
        'low': float(candle[3]),
        'close': float(candle[4]),
        'volume': float(candle[5])
    } for candle in candles])

def execute_trade(signal):
    if signal == 1:
        print("Executing Long Trade")
        client.place_order("open_long", SIZE)
    elif signal == -1:
        print("Executing Short Trade")
        client.place_order("open_short", SIZE)

def main_loop():
    # リスク管理スレッド起動
    risk_thread = threading.Thread(target=risk_manager.auto_manage)
    risk_thread.daemon = True
    risk_thread.start()
    
    while True:
        try:
            data = fetch_data()
            data = calculate_indicators(data)
            latest = data.iloc[-1]
            
            signal = ai_trader.predict(latest[['rsi', 'macd', 'ema20', 'ema50']])
            execute_trade(signal)
            
            # データ保存
            data.to_csv('data/historical.csv', mode='a', header=False, index=False)
            
            time.sleep(3600)  # 1時間間隔
        
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()