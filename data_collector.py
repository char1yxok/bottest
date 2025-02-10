# data_collector.py

import pandas as pd
import time
from datetime import datetime
from utils.api_client import BitgetClient
import config

def main():
    client = BitgetClient(config.API_KEY, config.SECRET_KEY, config.PASSPHRASE)
    symbol = config.SYMBOL
    granularity = config.GRANULARITY  # 1時間足（3600秒）

    # 取得するデータの期間を設定（例：過去200時間）
    data_points = 1000
    end_time = int(time.time() * 1000)  # 現在時刻（ミリ秒）
    start_time = end_time - (data_points * granularity * 1000)  # 開始時刻（ミリ秒）

    try:
        data = client.get_historical_data(symbol, granularity, start_time, end_time)

        # カラムをAPIドキュメントに基づいて指定
        df = pd.DataFrame(data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover'])

        # タイムスタンプを日時に変換
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        # データ型を適切に変換
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
        df[numeric_columns] = df[numeric_columns].astype(float)
        # CSVに保存
        df.to_csv('historical.csv', index=False)
        print("Data collected and saved to historical.csv.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()