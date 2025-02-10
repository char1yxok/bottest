# utils/deepseek_integration.py

import requests
import json
import config
import logging

class DeepSeekAPI:
    def __init__(self):
        self.base_url = config.DEEPSEEK_API_URL  # 例: 'http://localhost:11434/api/generate'
        self.model_name = config.DEEPSEEK_MODEL

    def train_model(self, prompt):
        """
        DeepSeekにトレーニング用のプロンプトを送信します。
        :param prompt: トレーニング用のプロンプト
        :return: 成功時はTrue、失敗時はFalse
        """
        url = self.base_url
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.model_name,
            'prompt': prompt,
            'stream': False,
            'stop_sequence': ["\n"]  # 必要に応じて設定
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            logging.debug(f"Training response: {result}")
            return True
        except requests.exceptions.Timeout:
            logging.error("Request timed out during model training.")
            return False
        except Exception as e:
            logging.error(f"Error during model training: {e}")
            return False

    def predict(self, prompt):
        """
        DeepSeekにプロンプトを送信して、予測結果を取得します。
        :param prompt: 予測用のプロンプト
        :return: 予測結果（辞書形式）
        """
        url = self.base_url
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.model_name,
            'prompt': prompt,
            'stream': False,
            'format': 'json'
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # DeepSeekからの応答を取得
            response_text = result.get('response', '')

            # レスポンスを辞書に変換
            # 余分な空白や特殊文字を除去
            response_text = response_text.strip()

            # JSONパース
            response_data = json.loads(response_text)
            return response_data
        except Exception as e:
            logging.error(f"Error during prediction: {e}")
            return None