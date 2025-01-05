from openalgo import api
import pandas as pd
import time
from datetime import datetime, timedelta

# Get API key from OpenAlgo portal
api_key = '42c3510f21af4329d48d0e9d6491bf09bdefbf8008ee9516776d78f7b3474e7f'

# Set the strategy details and trading parameters
strategy = "EMA Crossover Python"
symbol = "BHEL"  # OpenAlgo Symbol
exchange = "NSE"
product = "MIS"
quantity = 1

# EMA periods
fast_period = 3
slow_period = 100

# Set the API Key
client = api(api_key=api_key, host='http://127.0.0.1:7000')

def calculate_ema_signals(df):
    """
    Calculate EMA crossover signals.
    """
    close = df['close']
    # Calculate EMAs
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()

    # Generate crossover signals
    crossover = (ema_fast.shift(1) < ema_slow.shift(1)) & (ema_fast > ema_slow)
    crossunder = (ema_fast.shift(1) > ema_slow.shift(1)) & (ema_fast < ema_slow)

    return pd.DataFrame({
        'EMA_Fast': ema_fast,
        'EMA_Slow': ema_slow,
        'Crossover': crossover,
        'Crossunder': crossunder
    }, index=df.index)

def ema_strategy():
    """
    The EMA crossover trading strategy with 0.20% stop-loss.
    """
    position = 0
    stop_loss = None

    while True:
        try:
            # Dynamic date range: 7 days back to today
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            # Fetch 1-minute historical data using OpenAlgo
            df = client.history(
                symbol=symbol,
                exchange=exchange,
                interval="1m",
                start_date=start_date,
                end_date=end_date
            )

            # Check for valid data
            if df.empty:
                print("DataFrame is empty. Retrying...")
                time.sleep(15)
                continue

            # Verify required columns
            if 'close' not in df.columns:
                raise KeyError("Missing 'close' column in DataFrame")

            # Round the close column
            df['close'] = df['close'].round(2)

            # Calculate EMAs and signals
            signals = calculate_ema_signals(df)

            # Get the latest signals
            crossover = signals['Crossover'].iloc[-2]
            crossunder = signals['Crossunder'].iloc[-2]
            last_price = df['close'].iloc[-1]

            # Execute Buy Order
            if crossover and position <= 0:
                position = quantity
                stop_loss = last_price * 0.998  # Set stop-loss at 0.20% below entry price
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="BUY",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity
                )
                print("Buy Order Response:", response)

            # Execute Sell Order if stop-loss is hit (for Buy position)
            elif position > 0 and last_price <= stop_loss:
                position = 0
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="SELL",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity
                )
                print("Stop-Loss Hit. Sell Order Response:", response)

            # Execute Short-Sell Order
            elif crossunder and position >= 0:
                position = -quantity
                stop_loss = last_price * 1.002  # Set stop-loss at 0.20% above entry price for short sell
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="SELL",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity
                )
                print("Short-Sell Order Response:", response)

            # Execute Buy Order if stop-loss is hit (for Short-Sell position)
            elif position < 0 and last_price >= stop_loss:
                position = 0
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="BUY",
                    exchange=exchange,
                    price_type="MARKET",
                    product=product,
                    quantity=quantity
                )
                print("Stop-Loss Hit. Buy Order Response:", response)

            # Log strategy information
            print("\nStrategy Status:")
            print("-" * 50)
            print(f"Position: {position}")
            print(f"Last Price: {last_price}")
            print(f"Stop-Loss: {stop_loss}")
            print(f"Fast EMA ({fast_period}): {signals['EMA_Fast'].iloc[-2]:.2f}")
            print(f"Slow EMA ({slow_period}): {signals['EMA_Slow'].iloc[-2]:.2f}")
            print(f"Buy Signal: {crossover}")
            print(f"Sell Signal: {crossunder}")
            print("-" * 50)

        except Exception as e:
            print(f"Error in strategy: {str(e)}")
            time.sleep(15)
            continue

        # Wait before the next cycle
        time.sleep(15)

if __name__ == "__main__":
    print(f"Starting {fast_period}/{slow_period} EMA Crossover Strategy...")
    ema_strategy()
