# config.py

API_KEY = ""
SECRET_KEY = ""
PASSPHRASE = ""

# 取引設定
SYMBOL = 'BTCUSDT_UMCBL'  # USDT-M無期限契約のシンボル
MARGIN_COIN = 'USDT'  # 証拠金通貨
LEVERAGE = 125  # レバレッジ（必要に応じて調整）

DEEPSEEK_MODEL = "deepseek-r1:8b"
DEEPSEEK_API_URL = 'http://localhost:11434/api/generate'  # DeepseekのAPIエンドポイント

GRANULARITY = 3600  # キャンドル足の時間間隔（秒）：1時間足