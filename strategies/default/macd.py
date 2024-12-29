from openalgo import api
import pandas as pd
import numpy as np
import time
import threading
from datetime import datetime, timedelta

# Get API key from openalgo portal
api_key = '42c3510f21af4329d48d0e9d6491bf09bdefbf8008ee9516776d78f7b3474e7f'

# Set the strategy details and trading parameters
strategy = "MACD + EMA Strategy"
symbols = ["ARVIND", "HFCL", "PFC", "HINDALCO", "NCC", "NTPC"]  # List of symbols
exchange = "NSE"
product = "MIS"
quantity = 1

# MACD and EMA parameters
macd_short_period = 12
macd_long_period = 26
macd_signal_period = 9
ema_short_period = 4
ema_long_period = 19

# Set the API Key
client = api(api_key=api_key, host='http://127.0.0.1:7000')


def calculate_macd(df, short_period, long_period, signal_period):
    """
    Calculate MACD and Signal Line.
    """
    df['EMA_Short'] = df['close'].ewm(span=short_period, adjust=False).mean()
    df['EMA_Long'] = df['close'].ewm(span=long_period, adjust=False).mean()
    df['MACD'] = df['EMA_Short'] - df['EMA_Long']
    df['Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    return df


def calculate_ema(df, short_period, long_period):
    """
    Calculate EMA for given short and long periods.
    """
    df['EMA_4'] = df['close'].ewm(span=short_period, adjust=False).mean()
    df['EMA_19'] = df['close'].ewm(span=long_period, adjust=False).mean()
    return df


def macd_ema_strategy(symbol):
    """
    The MACD bullish crossover strategy with additional EMA crossover condition.
    Includes exit condition at 4% profit or loss.
    """
    position = 0
    entry_price = None

    while True:
        try:
            # Dynamic date range: 7 days back to today
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            # Fetch 5-minute historical data
            df = client.history(
                symbol=symbol,
                exchange=exchange,
                interval="5m",
                start_date=start_date,
                end_date=end_date
            )

            # Check for valid data
            if df.empty:
                print(f"DataFrame for {symbol} is empty. Retrying...")
                time.sleep(15)
                continue

            # Verify required columns
            expected_columns = {'close', 'high', 'low', 'open'}
            missing_columns = expected_columns - set(df.columns)
            if missing_columns:
                raise KeyError(f"Missing columns in DataFrame for {symbol}: {missing_columns}")

            # Round the close column
            df['close'] = df['close'].round(2)

            # Calculate MACD and EMA
            df = calculate_macd(df, macd_short_period, macd_long_period, macd_signal_period)
            df = calculate_ema(df, ema_short_period, ema_long_period)

            # Check for MACD bullish crossover
            macd = df['MACD']
            signal = df['Signal']
            bullish_crossover = macd.iloc[-2] <= signal.iloc[-2] and macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-1] > 0

            # Check for EMA crossover
            ema_4 = df['EMA_4']
            ema_19 = df['EMA_19']
            ema_crossover = ema_4.iloc[-2] <= ema_19.iloc[-2] and ema_4.iloc[-1] > ema_19.iloc[-1]

            # Execute Buy Order
            if bullish_crossover and ema_crossover and position <= 0:
                position = quantity
                entry_price = df['close'].iloc[-1]
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="BUY",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity,
                    position_size=position
                )
                print(f"Buy Order Response for {symbol}: {response}")

            # Monitor for Exit Condition
            if position > 0 and entry_price is not None:
                current_price = df['close'].iloc[-1]
                profit_loss_percentage = ((current_price - entry_price) / entry_price) * 100

                # Check if exit condition is met
                if profit_loss_percentage >= 4 or profit_loss_percentage <= -4:
                    response = client.placesmartorder(
                        strategy=strategy,
                        symbol=symbol,
                        action="SELL",
                        exchange=exchange,
                        price_type="MARKET",
                        product=product,
                        quantity=quantity,
                        position_size=-position
                    )
                    print(f"Sell Order Response for {symbol}: {response}")
                    print(f"Exit Condition Met: P&L = {profit_loss_percentage:.2f}%")
                    position = 0
                    entry_price = None

            # Log strategy information
            print(f"\nStrategy Status for {symbol}:")
            print("-" * 50)
            print(f"Position: {position}")
            print(f"LTP: {df['close'].iloc[-1]}")
            print(f"MACD: {macd.iloc[-1]:.2f}")
            print(f"Signal: {signal.iloc[-1]:.2f}")
            print(f"EMA_4: {ema_4.iloc[-1]:.2f}")
            print(f"EMA_19: {ema_19.iloc[-1]:.2f}")
            print(f"Entry Price: {entry_price}")
            print(f"P&L (%): {profit_loss_percentage if entry_price else 'N/A'}")
            print("-" * 50)

        except Exception as e:
            print(f"Error in strategy for {symbol}: {str(e)}")
            time.sleep(15)
            continue

        # Wait before the next cycle
        time.sleep(15)


def start_trading():
    """
    Start trading for multiple symbols.
    """
    threads = []

    for symbol in symbols:
        thread = threading.Thread(target=macd_ema_strategy, args=(symbol,))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    print("Starting MACD + EMA Strategy for multiple symbols...")
    start_trading()
