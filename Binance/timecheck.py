import requests
import datetime
import pytz

# Binance API endpoint for server time
BINANCE_TIME_URL = "https://api.binance.com/api/v3/time"

# Binance API endpoint for historical price data
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"

# Fetch Binance server time
response = requests.get(BINANCE_TIME_URL)
server_time_ms = response.json()["serverTime"]  # Binance time in milliseconds

# Convert Binance server time to readable format
server_time_utc = datetime.datetime.fromtimestamp(server_time_ms / 1000, datetime.UTC)
server_time_local = server_time_utc.astimezone()  # Converts to local system time

print(f"🔹 Binance Server Time (Milliseconds): {server_time_ms}")
print(f"🔹 Binance Server Time (UTC): {server_time_utc}")
print(f"🔹 Binance Server Time (Local Time): {server_time_local}")

# --- Fetch historical price data for ETH/USDC ---
params = {
    "symbol": "ETHUSDC",
    "interval": "1h",
    "limit": 1  # Get the most recent 1-hour data point
}

response = requests.get(BINANCE_KLINES_URL, params=params)
ohlc_data = response.json()

# Extract the open time (first value in the returned list)
open_time_ms = ohlc_data[0][0]  # Open time in milliseconds
open_time_utc = datetime.datetime.fromtimestamp(open_time_ms / 1000, datetime.UTC)
open_time_local = open_time_utc.astimezone()

print(f"\n🔹 Binance Kline Open Time (Milliseconds): {open_time_ms}")
print(f"🔹 Binance Kline Open Time (UTC): {open_time_utc}")
print(f"🔹 Binance Kline Open Time (Local Time): {open_time_local}")

# Compare with system UTC and local time
current_utc = datetime.datetime.now(pytz.utc)
current_local = datetime.datetime.now()

print(f"\n🔹 System Current Time (UTC): {current_utc}")
print(f"🔹 System Current Time (Local): {current_local}")
