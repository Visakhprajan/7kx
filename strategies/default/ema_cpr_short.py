from openalgo import api
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Get API key from OpenAlgo portal
api_key = '42c3510f21af4329d48d0e9d6491bf09bdefbf8008ee9516776d78f7b3474e7f'

# Strategy parameters
strategy = "EMA & CPR Python"
symbol = "AUBANK"  # OpenAlgo Symbol
exchange = "NSE"
product = "MIS"
quantity = 1  # Single lot
fast_period = 100  # EMA period
trade_price = 552.00  # Target price for entry
target_pct = 0.009 
target_price = round(trade_price * (1 - 0.009) * 20) / 20  # Rounding to nearest 5 paise
stop_loss_pct = 0.003  # 0.3% stop-loss (in decimal)
stop_loss_price = round(trade_price * (1 + 0.003) * 20) / 20  # 0.3%  # Rounding to nearest 5 paise
# Initialize API client
print(f"Target Price: {target_price:.2f}")
print(f"Stop loss Price: {stop_loss_price:.2f}")

client = api(api_key=api_key, host='http://127.0.0.1:7000')


def calculate_ema(df, period):
    """
    Calculate EMA for the given period.
    """
    return df['close'].ewm(span=period, adjust=False).mean()


def ema_strategy():
    """
    The EMA-based trading strategy.
    """
    position = 0  # Track position
    entry_price = None  # Track entry price

    while True:
        try:
            # Fetch historical data for the last 7 days
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            df = client.history(
                symbol=symbol,
                exchange=exchange,
                interval="15m",
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                print("DataFrame is empty. Retrying...")
                time.sleep(15)
                continue

            # Prepare data
            df['close'] = df['close'].round(2)
            df['EMA_100'] = calculate_ema(df, fast_period)

            # Get the latest LTP and EMA
            ltp = df['close'].iloc[-1]
            ema_100 = df['EMA_100'].iloc[-1]

            print(f"\nLatest Data: LTP={ltp}, EMA_100={ema_100:.2f}")

            # Buy Condition
            if ltp < ema_100 and ltp == trade_price and position == 0:
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="SELL",
                    exchange=exchange,
                    price_type="LIMIT",
                    price=trade_price,
                    product=product,
                    quantity=quantity,
                    position_size=position
                )
                print("Sell Order Response:", response)
                position = quantity
                entry_price = ltp

            # Target Condition
            if position > 0 and ltp >= entry_price * (1 - target_pct):
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="BUY",
                    exchange=exchange,
                    price_type="LIMIT",
                    price=target_price,
                    product=product,
                    quantity=position
                )
                print("Target Triggered. Sell Order Response:", response)
                position = 0  # Reset position
                entry_price = None  # Reset entry price

            # Stop-Loss Condition
            if position > 0 and ltp <= entry_price * (1 + stop_loss_pct):
                response = client.placesmartorder(
                    strategy=strategy,
                    symbol=symbol,
                    action="BUY",
                    exchange=exchange,
                    price_type="LIMIT",
                    price=stop_loss_price,
                    product=product,
                    quantity=position
                )
                print("Stop-Loss Triggered. Sell Order Response:", response)
                position = 0  # Reset position
                entry_price = None  # Reset entry price

            # Log strategy status
            print(f"Position: {position}, Entry Price: {entry_price}, LTP: {ltp}, EMA_100: {ema_100:.2f}")

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(15)  # Retry after a delay

        time.sleep(15)  # Wait for the next iteration


if __name__ == "__main__":
    print(f"Starting EMA (100) Strategy with Trade Price {trade_price}...")
    ema_strategy()
