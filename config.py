# config.py
API_KEY = ""
SECRET_KEY = ""
PASSPHRASE = ""
SYMBOL = "BTCUSDT_UMCBL"  # 取引対象のシンボル
PRODUCT_TYPE = "UMCBL"      # USDT-Margined Contracts
MARGIN_MODE = "crossed"     # クロスマージン
LEVERAGE = 125       # レバレッジ
SIZE = 0.001     # 取引数量
DEEPSEEK_MODEL = "deepseek-r1:8b"  # Ollamaで使用するモデル名
TIMEFRAME = "1H"            # 1時間足
MODEL_PATH = "data/models/trade_model.pkl"