import time
import pandas as pd
import numpy as np
from datetime import datetime
from openalgo import api

# Initialize the API client
api_key = '42c3510f21af4329d48d0e9d6491bf09bdefbf8008ee9516776d78f7b3474e7f'
client = api(api_key=api_key, host='http://127.0.0.1:7000')

# Define trading parameters
strategy = "RSI Strategy"
symbols = ["ARVIND", "HFCL", "NCC", "NTPC", "OIL"]
exchange = "NSE"
product = "MIS"
quantity = 1

# RSI calculation function
def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to fetch 5-minute candle data
def fetch_candle_data(symbol, interval="5min", limit=100):
    response = client.get_candles(symbol=symbol, exchange=exchange, interval=interval, limit=limit)
    if response['status'] == 'success':
        return pd.DataFrame(response['data'])
    else:
        print(f"Error fetching data for {symbol}: {response['message']}")
        return None

# Function to execute trades
def execute_trade(symbol, action):
    response = client.place_order(
        symbol=symbol,
        exchange=exchange,
        product=product,
        transaction_type=action,
        quantity=quantity,
        order_type="MARKET"
    )
    print(f"Order response for {symbol} - {action}: {response}")

# Trading logic for RSI strategy
def rsi_strategy():
    for symbol in symbols:
        data = fetch_candle_data(symbol)
        if data is not None and len(data) > 14:
            data['rsi'] = calculate_rsi(data)
            latest_rsi = data['rsi'].iloc[-1]
            print(f"{symbol} - Latest RSI: {latest_rsi}")

            if latest_rsi <= 30:
                execute_trade(symbol, "BUY")
            elif latest_rsi >= 70:
                execute_trade(symbol, "SELL")

# Main trading loop
if __name__ == "__main__":
    print("Starting RSI strategy...")
    while True:
        try:
            rsi_strategy()
            time.sleep(300)  # Wait for 5 minutes before checking again
        except Exception as e:
            print(f"Error: {e}")
