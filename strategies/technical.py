import pandas as pd
import ta

def calculate_indicators(data):
    data['rsi'] = ta.momentum.RSIIndicator(data['close'], window=14).rsi()
    macd = ta.trend.MACD(data['close'], window_slow=26, window_fast=12, window_sign=9)
    data['macd'] = macd.macd()
    data['macd_signal'] = macd.macd_signal()
    data['ema20'] = ta.trend.EMAIndicator(data['close'], window=20).ema_indicator()
    data['ema50'] = ta.trend.EMAIndicator(data['close'], window=50).ema_indicator()
    return data