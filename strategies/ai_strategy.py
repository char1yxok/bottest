import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from .technical import calculate_indicators
from strategies.deepseek_integration import DeepSeekAdapter

class AITrader:
    MODEL_PATH = 'data/models/trade_model.pkl'
    def __init__(self):
        self.model = None
        self.deepseek = DeepSeekAdapter()  # DeepSeek連携追加
        self.load_model()
    
    def load_model(self):
        try:
            self.model = joblib.load(self.MODEL_PATH)
        except FileNotFoundError:
            self.model = RandomForestClassifier(n_estimators=100)
            self.initial_training()
    
    def initial_training(self):
        data = pd.read_csv('data/historical.csv')
        data = calculate_indicators(data)
        # DeepSeekでラベル生成
        labels = []
        for _, row in data.iterrows():
            try:
                result = self.deepseek.get_trading_signal(row.to_dict())
                print(result)
                labels.append(1 if result['signal'] == 'BUY' else -1 if result['signal'] == 'SELL' else 0)
            except:
                print("エラーーーーーー")
        print("AAA")
        data['signal'] = labels
        print("AAB")
        self.train(data)
    
    def generate_labels(self, data):
        labels = []
        for i in range(1, len(data)):
            if data['close'].iloc[i] > data['close'].iloc[i-1]:
                labels.append(1)  # Buy
            else:
                labels.append(-1) # Sell
        labels.append(0)  # 最後のデータポイント用
        return labels
    
    def train(self, data):
        print("ABA")
        X = data[['rsi', 'macd', 'ema20', 'ema50']]
        print("ABC")
        y = data['signal']
        print(data)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        # self.model.fit(X_train, y_train)
        # モデルファイルが存在するか確認
        print("BBB")
        if os.path.exists(self.MODEL_PATH):
            print("CCC")
            self.model = joblib.load(self.MODEL_PATH)
            joblib.dump(self.model, self.MODEL_PATH)
        else:
            print("DDD")
            print("モデルファイルが存在しません。新しいモデルを作成してください。")
            
            # 保存先のディレクトリパス
            directory = 'data/models/'
        
            # ディレクトリが存在しない場合は作成する
            os.makedirs(directory, exist_ok=True)
        
            # モデルを指定したパスに保存する
            joblib.dump(self.model, os.path.join(directory, 'trade_model.pkl'))
        #joblib.dump(self.model, 'data/models/trade_model.pkl')
    
    def predict(self, data):
        return self.model.predict([data])[0]