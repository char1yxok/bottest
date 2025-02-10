import hashlib
import hmac
import time
import requests
import json
from urllib.parse import urlencode

from config import LEVERAGE, MARGIN_MODE, PRODUCT_TYPE, SYMBOL

class BitgetClient:
    BASE_URL = "https://api.bitget.com"
    
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Bitget-API/3.0"
        })

    def _sign(self, message):
        return hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _auth_headers(self, method, path, params=None):
        timestamp = str(int(time.time() * 1000))
        message = timestamp + method.upper() + path
        
        if method == "GET" and params:
            sorted_params = sorted(params.items())
            message += "?" + urlencode(sorted_params)
        elif method == "POST" and params:
            message += json.dumps(params)
        
        signature = self._sign(message)
        
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
        }

    def get_candles(self, symbol, timeframe, limit=100):
        path = "/api/v2/market/candles"
        params = {
            "symbol": symbol,
            "granularity": timeframe,
            "limit": limit
        }
        
        #headers = self._auth_headers("GET", path, params)
        response = self.session.get(
            self.BASE_URL + path,
            params=params,
            #headers=headers
        )
        print(response)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            raise Exception(f"API Error: {response}")

    def place_order(self, side, size):
        path = "/api/v2/mix/order/place-order"
        params = {
            "symbol": SYMBOL,
            "productType": PRODUCT_TYPE,
            "marginMode": "crossed",
            "marginCoin": MARGIN_MODE,
            "size": str(size),
            "side": side,
            "orderType": "market",
            "leverage": str(LEVERAGE)
        }
        
        headers = self._auth_headers("POST", path, params)
        response = self.session.post(
            self.BASE_URL + path,
            json=params,
            headers=headers
        )
        return response.json()

    def get_positions(self):
        path = "/api/v2/mix/position/all-position"
        params = {
            "productType": PRODUCT_TYPE,
            "marginCoin": MARGIN_MODE
        }
        
        headers = self._auth_headers("GET", path, params)
        response = self.session.get(
            self.BASE_URL + path,
            params=params,
            headers=headers
        )
        return response.json().get("data", [])

    def close_position(self, position):
        path = "/api/v2/mix/order/close-position"
        params = {
            "symbol": SYMBOL,
            "marginCoin": MARGIN_MODE,
            "holdSide": position["holdSide"],
            "size": position["total"]
        }
        
        headers = self._auth_headers("POST", path, params)
        response = self.session.post(
            self.BASE_URL + path,
            json=params,
            headers=headers
        )
        return response.json()