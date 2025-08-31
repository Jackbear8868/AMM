import requests
import pandas as pd
import datetime
import time

# Define the base URL and endpoint for Binance API
BASE_URL = "https://api.binance.com/api/v3"
ENDPOINT = "/klines"

# Define the trading pair and interval
symbol = "ETHUSDT"
interval = "1s"  # 1-hour candlesticks

# Convert start and end dates to UTC timestamps in milliseconds
start_time = int(datetime.datetime(2023, 12, 30, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
end_time = int(datetime.datetime(2024, 1, 2, 0, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)

start = time.time()

print(f"Fetching data from {datetime.datetime.fromtimestamp(start_time/1000, datetime.timezone.utc)} UTC "
      f"to {datetime.datetime.fromtimestamp(end_time/1000, datetime.timezone.utc)} UTC")

# Function to fetch data in batches
def fetch_data(start_time, end_time, symbol, interval):
    all_data = []
    
    while start_time < end_time:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1000  # Binance API allows max 1000 per request
        }

        response = requests.get(BASE_URL + ENDPOINT, params=params)

        if response.status_code == 200:
            data = response.json()
            if not data:
                break  # No more data available

            # Append data to the list
            all_data.extend(data)

            # Move to the next batch (next timestamp after the last one)
            last_timestamp = data[-1][0]
            if last_timestamp == start_time:  # Prevent infinite loops if no progress is made
                break
            start_time = last_timestamp + 1  # Avoid duplicate entries

            # Respect API rate limits
            time.sleep(0.1)
        else:
            print(f"Error: Unable to fetch data. Status code {response.status_code}")
            break

    return all_data

# Fetch data from Binance API
data = fetch_data(start_time, end_time, symbol, interval)


if not data:
    print("No data retrieved. Check your parameters or API limits.")
    exit()

# Extract relevant columns: Open Time and Close Price
columns = ["Open Time", "Close Price"]
extracted_data = [[item[0], float(item[4])] for item in data]

# Create DataFrame
df = pd.DataFrame(extracted_data, columns=columns)

# Convert timestamps to readable UTC datetime format
df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms", utc=True).dt.tz_localize(None)

end = time.time()
print(f"cost time: {end - start}")

# Ensure no boundary issues by checking the first and last rows
print(f"First timestamp: {df.iloc[0]['Open Time']}")
print(f"Last timestamp: {df.iloc[-1]['Open Time']}")

# Save to CSV
df.to_csv(f"{symbol}_{interval}.csv", index=False)

print(f"✅ Data successfully saved to {symbol}_{interval}.csv")
