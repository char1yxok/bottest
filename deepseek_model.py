# deepseek_model.py

import os
import pandas as pd
import numpy as np
from utils.deepseek_integration import DeepSeekAPI
import logging
from tqdm import tqdm  # 進捗バー表示のために追加

class DeepSeekModel:
    def __init__(self, model_dir='data/models', model_filename='model_state.txt'):
        self.model_dir = model_dir
        self.model_filename = model_filename
        self.model_path = os.path.join(self.model_dir, self.model_filename)
        self.model = None  # DeepSeekを使用するため、モデルオブジェクトは必要ない
        self.api = DeepSeekAPI()

        # モデルディレクトリが存在しない場合は作成
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
            logging.info(f"Created model directory: {self.model_dir}")

    def load_model(self):
        # モデルが利用可能かどうかをフラグで管理
        if os.path.exists(self.model_path):
            logging.info("Model is available.")
            self.model = True  # モデルが利用可能であることを示すフラグ
        else:
            logging.info("No existing model found.")
            self.model = None

    def save_model(self):
        # モデルの存在を示すためのファイルを作成
        with open(self.model_path, 'w') as f:
            f.write('Model is trained')  # 内容は特に意味を持ちません
        logging.info("Model state file saved.")

    def train(self, data):
        # トレーニングデータを1件ずつDeepSeekに送信
        logging.info("Starting training data sending...")
        success = True

        total_samples = len(data)  # 100件のはずです

        # tqdmを使用して進捗バーを表示
        for index, row in tqdm(data.iterrows(), total=total_samples, desc="Sending training data"):
            # 各行のデータを使用してプロンプトを作成
            training_prompt = self.create_training_prompt(row)
            # DeepSeekにトレーニングデータを送信
            result = self.api.train_model(training_prompt)
            if not result:
                success = False
                break  # エラーが発生した場合、ループを終了

        if success:
            logging.info("All training data sent successfully.")
            self.model = True  # モデルが利用可能になったと仮定
            # モデルの存在を示すファイルを保存
            self.save_model()
        else:
            logging.error("An error occurred during training data sending.")
            self.model = None

    def predict(self, market_data):
        # 必要なテクニカル指標のキーリスト
        required_keys = ['Close', 'RSI', 'MACD', 'MACD_Signal', 'EMA20', 'EMA50', 'EMA200', 'BB_upper', 'BB_middle', 'BB_lower']

        # キーが存在するか確認
        for key in required_keys:
            if key not in market_data or pd.isna(market_data[key]):
                logging.error(f"Key '{key}' not found or NaN in market_data.")
                return None, 0, f"Missing key '{key}' in market_data."

        # プロンプトを作成
        prompt = self.create_prediction_prompt(market_data)
        # DeepSeekに予測を依頼
        result = self.api.predict(prompt)
        if result:
            signal = result.get('signal')
            confidence = float(result.get('confidence', 0))
            reason = result.get('reason', '')
            return signal, confidence, reason
        else:
            return None, 0, "DeepSeekからの応答なし"

    def create_training_prompt(self, data_row):
        # 1件のデータを使用してトレーニング用のプロンプトを作成
        prompt = f"""【トレーニングデータ】
時間: {data_row['Timestamp']}
価格: {data_row['Close']}
Open: {data_row['Open']}, High: {data_row['High']}, Low: {data_row['Low']}
Volume: {data_row['Volume']}, Turnover: {data_row['Turnover']}

このデータを使用して、今後の市場動向を予測するモデルを学習してください。
"""
        return prompt

    def create_prediction_prompt(self, market_data):
        # 予測用のプロンプトを作成するためのメソッド
        prompt = f"""【仮想通貨取引分析】
現在のBTC/USDT先物データ（1時間足）:
- 価格: {market_data['Close']}
- RSI(14): {market_data['RSI']:.2f}
- MACD(12,26,9): {market_data['MACD']:.2f} (Signal: {market_data['MACD_Signal']:.2f})
- EMA(20/50/200): {market_data['EMA20']:.2f}/{market_data['EMA50']:.2f}/{market_data['EMA200']:.2f}
- ボリンジャーバンド: Upper {market_data['BB_upper']:.2f}, Middle {market_data['BB_middle']:.2f}, Lower {market_data['BB_lower']:.2f}

リスク管理ルール:
- 最大レバレッジ: {market_data.get('Leverage', '125x')}
- 利確: +5%
- 損切り: -3%

現在の市場環境を分析し、以下の選択肢から最適な行動を選んでください:
1. ロングポジションを開く（BUY）
2. ショートポジションを開く（SELL）
3. ホールド（HOLD）

出力形式（JSONのみ）:
{{
    "signal": "BUY|SELL|HOLD",
    "confidence": 0.0-1.0,
    "reason": "分析理由"
}}
"""
        return prompt

    def calculate_indicators(self, df):
        # データが不足していないか確認
        min_periods_required = 100  # 必要な最低データポイント数
        if len(df) < min_periods_required:
            raise Exception(f"Insufficient data for calculating indicators. Need at least {min_periods_required} data points.")

        # インデックスをTimestampに設定
        df = df.set_index('Timestamp')

        # データを昇順に並べ替え（古いデータから新しいデータへ）
        df = df.sort_index()

        # 欠損値の処理
        df = df.dropna()

        # RSIの計算
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, -0.0)
        avg_gain = gain.rolling(window=14, min_periods=14).mean()
        avg_loss = loss.rolling(window=14, min_periods=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # EMAの計算
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # MACDの計算
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # ボリンジャーバンドの計算
        df['BB_middle'] = df['Close'].rolling(window=20, min_periods=20).mean()
        df['BB_std'] = df['Close'].rolling(window=20, min_periods=20).std()
        df['BB_upper'] = df['BB_middle'] + (df['BB_std'] * 2)
        df['BB_lower'] = df['BB_middle'] - (df['BB_std'] * 2)

        # テクニカル指標計算後、欠損値を削除
        df = df.dropna()

        # インデックスをリセット
        df = df.reset_index()

        return df