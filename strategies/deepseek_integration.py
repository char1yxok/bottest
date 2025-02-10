import requests
import json
from config import DEEPSEEK_MODEL

class DeepSeekAdapter:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
    
    REQUIRED_FEATURES = [
        'rsi', 'macd', 'macd_signal', 'macd_diff',
        'ema20', 'ema50', 'ema200',
        'bb_upper', 'bb_middle', 'bb_lower'
    ]

    def get_trading_signal(self, market_data):
        """入力データ検証付き信号生成"""
        # 入力データ検証
        missing = [f for f in self.REQUIRED_FEATURES if f not in market_data]
        if missing:
            raise ValueError(f"必須指標が不足: {missing}")

        prompt = f"""【仮想通貨取引分析】
        現在のBTC/USDT先物データ（1時間足）:
        - 価格: {market_data['close']}
        - RSI(14): {market_data['rsi']:.2f}
        - MACD(12,26,9): {market_data['macd']:.2f} (Signal: {market_data['macd_signal']:.2f})
        - EMA(20/50/200): {market_data['ema20']:.2f}/{market_data['ema50']:.2f}/{market_data['ema200']:.2f}
        - ボリンジャーバンド: Upper {market_data['bb_upper']:.2f}, Middle {market_data['bb_middle']:.2f}, Lower {market_data['bb_lower']:.2f}

        リスク管理ルール:
        - 最大レバレッジ: 20x
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
        
        response = requests.post(
            self.base_url,
            json={
                "model": DEEPSEEK_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
        )
        try:
            return json.loads(response.json()['response'])
        except:
            return {"signal": "HOLD", "reason": "解析エラー"}