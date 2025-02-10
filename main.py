# main.py

import time
import pandas as pd
import numpy as np
from utils.api_client import BitgetClient
from deepseek_model import DeepSeekModel
import config
import threading
import datetime
import logging

def main():
    # ログの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    client = BitgetClient(config.API_KEY, config.SECRET_KEY, config.PASSPHRASE)
    model = DeepSeekModel()

    position = None  # 現在のポジション情報を管理

    # 前回のモデル再訓練の時刻を記録
    last_training_time = datetime.datetime.utcnow()

    # モデルの初回ロード
    model.load_model()
    if model.model is None:
        # 初回学習を実行
        logging.info("Training the model for the first time...")
        retrain_model(model)
        last_training_time = datetime.datetime.utcnow()

    while True:
        try:
            current_time = datetime.datetime.utcnow()
            # 追加学習のタイミングをチェック（例：毎日）
            if (current_time - last_training_time).total_seconds() >= 60:  # 86400秒 = 24時間
                logging.info("Starting model retraining...")
                retrain_thread = threading.Thread(target=retrain_model, args=(model,))
                retrain_thread.start()
                last_training_time = current_time

            logging.info("Starting new cycle.")

            # 最新のデータを取得
            symbol = config.SYMBOL
            granularity = config.GRANULARITY  # 1時間足

            end_time = int(time.time() * 1000)  # 現在時刻（ミリ秒）
            start_time = end_time - (100 * granularity * 1000)  # 過去200本分のデータ

            data = client.get_historical_data(symbol, granularity, start_time, end_time)
            df = pd.DataFrame(data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover'])
            df['Timestamp'] = pd.to_numeric(df['Timestamp'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
            df[numeric_columns] = df[numeric_columns].astype(float)

            # テクニカル指標の計算
            df = model.calculate_indicators(df)

            # テクニカル指標計算後、データが存在するか確認
            if df.empty:
                logging.error("No data available after calculating indicators.")
                return  # 必要に応じて処理を中断

            # 最新のデータを抽出
            latest_data = df.iloc[-1]

            current_price = latest_data['Close']

            if position is None:
                # ポジションがない場合、予測の実行
                logging.info("Predicting market trend using DeepSeek.")
                signal, confidence, reason = model.predict(latest_data)
                logging.info(f"Prediction result - Signal: {signal}, Confidence: {confidence}, Reason: {reason}")

                # 取引の判断と実行
                if signal == 'BUY':
                    # 買いポジションを開く
                    logging.info(f"Opening a long position (confidence: {confidence}): {reason}")
                    open_price = current_price
                    size = 0.005  # 適切なサイズを設定
                    client.place_order('open_long', size=size)
                    # 利確・損切り価格を設定
                    take_profit_price = open_price * 1.01  # 利確: +5%
                    stop_loss_price = open_price * 0.98    # 損切り: -3%
                    position = {
                        'side': 'long',
                        'size': size,
                        'open_price': open_price,
                        'take_profit_price': take_profit_price,
                        'stop_loss_price': stop_loss_price
                    }
                elif signal == 'SELL':
                    # 売りポジションを開く
                    logging.info(f"Opening a short position (confidence: {confidence}): {reason}")
                    open_price = current_price
                    size = 0.005  # 適切なサイズを設定
                    client.place_order('open_short', size=size)
                    # 利確・損切り価格を設定
                    take_profit_price = open_price * 0.98  # 利確: -5%
                    stop_loss_price = open_price * 1.02    # 損切り: +3%
                    position = {
                        'side': 'short',
                        'size': size,
                        'open_price': open_price,
                        'take_profit_price': take_profit_price,
                        'stop_loss_price': stop_loss_price
                    }
                else:
                    # 何もしない
                    logging.info(f"No trading signal (confidence: {confidence}): {reason}")
            else:
                # ポジションがある場合、利益確定や損切りをチェック
                logging.info(f"Managing open position: {position}")
                if position['side'] == 'long':
                    # ロングポジションの場合
                    if current_price >= position['take_profit_price']:
                        logging.info("Take profit triggered for long position.")
                        client.place_order('close_long', size=position['size'])
                        position = None
                    elif current_price <= position['stop_loss_price']:
                        logging.info("Stop loss triggered for long position.")
                        client.place_order('close_long', size=position['size'])
                        position = None
                elif position['side'] == 'short':
                    # ショートポジションの場合
                    if current_price <= position['take_profit_price']:
                        logging.info("Take profit triggered for short position.")
                        client.place_order('close_short', size=position['size'])
                        position = None
                    elif current_price >= position['stop_loss_price']:
                        logging.info("Stop loss triggered for short position.")
                        client.place_order('close_short', size=position['size'])
                        position = None

            logging.info("Cycle completed. Waiting for next cycle.")
            time.sleep(10)  # 10秒ごとにチェック

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}", exc_info=True)
            time.sleep(60)  # エラー発生時は1分待機して再試行

def retrain_model(model):
    try:
        logging.info("Retraining model using DeepSeek...")
        # 過去100本分のデータを取得
        symbol = config.SYMBOL
        granularity = config.GRANULARITY  # 1時間足

        end_time = int(time.time() * 1000)  # 現在時刻（ミリ秒）
        start_time = end_time - (100 * granularity * 1000)  # 過去100本分のデータ

        client = BitgetClient(config.API_KEY, config.SECRET_KEY, config.PASSPHRASE)
        data = client.get_historical_data(symbol, granularity, start_time, end_time)
        df = pd.DataFrame(data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Turnover'])
        df['Timestamp'] = pd.to_numeric(df['Timestamp'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Turnover']
        df[numeric_columns] = df[numeric_columns].astype(float)

        # テクニカル指標の計算
        df = model.calculate_indicators(df)

        # モデルの訓練
        model.train(df)

        logging.info("Model retrained successfully.")

    except Exception as e:
        logging.error(f"An error occurred during model retraining: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()