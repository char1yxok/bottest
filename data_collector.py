from utils.api_client import BitgetClient
from config import API_KEY, PRODUCT_TYPE, SECRET_KEY, PASSPHRASE, SYMBOL, TIMEFRAME
import pandas as pd
import time

client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)

def collect_historical_data(days=30):
    df = pd.DataFrame()
    end_time = None
    
    for _ in range(days * 24):  # 1時間足×日数×24時間
        params = {
            "symbol": SYMBOL,
            "productType": PRODUCT_TYPE,
            "granularity": TIMEFRAME,
            "limit": 100
        }
        
        if end_time:
            params["endTime"] = end_time
        
        candles = client.get_candles(SYMBOL, TIMEFRAME)
        if not candles:
            break
            
        batch_df = pd.DataFrame([{
            "timestamp": int(candle[0]),
            "open": float(candle[1]),
            "high": float(candle[2]),
            "low": float(candle[3]),
            "close": float(candle[4]),
            "volume": float(candle[5]),
            "quoteVolume": float(candle[6])
        } for candle in candles])
        
        df = pd.concat([df, batch_df])
        end_time = df['timestamp'].min() - 1
        time.sleep(0.5)
    
    df.sort_values('timestamp', inplace=True)
    df.to_csv('data/historical.csv', index=False)
    print(f"Collected {len(df)} historical records")

if __name__ == "__main__":
    collect_historical_data(30)