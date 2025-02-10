# utils/api_client.py

import logging
import time
import hashlib
import hmac
import requests
import base64
import json
import config

class BitgetClient:
    def __init__(self, api_key, secret_key, passphrase):
        self.base_url = 'https://api.bitget.com'
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def get_historical_data(self, symbol, granularity, startTime, endTime):
        method = 'GET'
        endpoint = '/api/mix/v1/market/candles'
        url = self.base_url + endpoint
        params = {
            'symbol': symbol,
            'granularity': str(granularity),
            'startTime': str(startTime),
            'endTime': str(endTime)
        }
    
        response = requests.get(url, params=params)
        
        # レスポンスの内容を出力（デバッグ用）
        logging.debug("API Response:")
        logging.debug(f"Status Code: {response.status_code}")
        logging.debug(f"Response Text: {response.text}")
    
        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError as e:
                logging.error(f"JSON parsing error: {e}")
                logging.error(f"Response Text: {response.text}")
                raise Exception("Failed to parse JSON response")
    
            if isinstance(data, dict):
                if data.get("code") == "00000":
                    candles = data.get("data")
                    if candles:
                        # データを新しい順から古い順に並べ替え
                        candles.reverse()
                        return candles
                    else:
                        raise Exception("No data available")
                else:
                    error_msg = data.get('msg', 'Unknown error')
                    raise Exception(f"API error: {error_msg}")
            elif isinstance(data, list):
                # データを新しい順から古い順に並べ替え
                data.reverse()
                return data
            else:
                raise Exception("Unexpected response format")
        else:
            logging.error(f"HTTP Error {response.status_code}: {response.text}")
            try:
                error_data = response.json()
                error_msg = error_data.get('msg', 'Unknown error')
            except ValueError:
                error_msg = response.text
            raise Exception(f"HTTP Error {response.status_code}: {error_msg}")

    def place_order(self, side, size, price=None):
        method = 'POST'
        endpoint = '/api/mix/v1/order/placeOrder'
        url = self.base_url + endpoint
        path = endpoint

        timestamp = str(int(time.time() * 1000))
        body = {
            "symbol": config.SYMBOL,
            "marginCoin": config.MARGIN_COIN,
            "orderType": "market" if price is None else "limit",
            "side": side,
            "size": str(size),
        }
        if price is not None:
            body["price"] = str(price)
        body_json = json.dumps(body)

        sign = self._generate_signature(timestamp, method, path, body_json)
        headers = {
            'Content-Type': 'application/json',
            'ACCESS-KEY': self.api_key,
            'ACCESS-SIGN': sign,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': self.passphrase,
        }

        response = requests.post(url, data=body_json, headers=headers)
        response.raise_for_status()

        data = response.json()
        if data.get("code") == "00000":
            return data["data"]
        else:
            raise Exception(f"API error: {data.get('msg')}")

    def set_leverage(self, leverage):
        method = 'POST'
        endpoint = '/api/mix/v1/account/setLeverage'
        url = self.base_url + endpoint
        path = endpoint

        timestamp = str(int(time.time() * 1000))
        body = {
            "symbol": config.SYMBOL,
            "marginCoin": config.MARGIN_COIN,
            "leverage": str(leverage),
            # crossモードでは holdSide は不要
        }
        body_json = json.dumps(body)

        sign = self._generate_signature(timestamp, method, path, body_json)
        headers = {
            'Content-Type': 'application/json',
            'ACCESS-KEY': self.api_key,
            'ACCESS-SIGN': sign,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': self.passphrase,
        }

        response = requests.post(url, data=body_json, headers=headers)
        if response.status_code != 200:
            try:
                error_message = response.json().get('msg', 'Unknown error')
            except Exception:
                error_message = response.text
            raise Exception(f"HTTP {response.status_code} Error: {error_message}")
        data = response.json()
        if data.get("code") == "00000":
            print(f"Leverage set to {leverage}x.")
        else:
            raise Exception(f"API error: {data.get('msg')}")

    def set_margin_mode(self, marginMode="crossed"):
        method = 'POST'
        endpoint = '/api/mix/v1/account/setMarginMode'
        url = self.base_url + endpoint
        path = endpoint

        timestamp = str(int(time.time() * 1000))
        body = {
            "symbol": config.SYMBOL,
            "marginCoin": config.MARGIN_COIN,
            "marginMode": marginMode
        }
        body_json = json.dumps(body)

        sign = self._generate_signature(timestamp, method, path, body_json)
        headers = {
            'Content-Type': 'application/json',
            'ACCESS-KEY': self.api_key,
            'ACCESS-SIGN': sign,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-PASSPHRASE': self.passphrase,
        }

        response = requests.post(url, data=body_json, headers=headers)
        if response.status_code != 200:
            try:
                error_message = response.json().get('msg', 'Unknown error')
            except Exception:
                error_message = response.text
            raise Exception(f"HTTP {response.status_code} Error: {error_message}")
        data = response.json()
        if data.get("code") == "00000":
            print(f"Margin mode set to {marginMode}.")
        else:
            raise Exception(f"API error: {data.get('msg')}")

    def _generate_signature(self, timestamp, method, request_path, body):
        message = f"{timestamp}{method}{request_path}{body}"
        mac = hmac.new(bytes(self.secret_key, 'utf-8'), bytes(message, 'utf-8'), hashlib.sha256)
        sign = base64.b64encode(mac.digest()).decode('utf-8')
        return sign