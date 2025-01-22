import requests
import pandas as pd
import datetime
import time

# Define the base URL and endpoint for Binance API
BASE_URL = "https://data-api.binance.vision/api/v3"
ENDPOINT = "/klines"

# Define the trading pair and other parameters
symbol = "ETHUSDC"
interval = "1m"  # Minute interval
start_date = "2023-12-30"
end_date = "2025-01-02"

# Convert the start and end dates to milliseconds since Unix epoch
start_time = int(datetime.datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
end_time = int(datetime.datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)

# Function to fetch data in chunks
def fetch_data(start_time, end_time, symbol, interval):
    all_data = []
    while start_time < end_time:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1000  # Maximum number of data points per request
        }

        response = requests.get(BASE_URL + ENDPOINT, params=params)

        if response.status_code == 200:
            data = response.json()
            if not data:
                break

            # Add data to the list
            all_data.extend(data)

            # Update start_time to fetch the next batch
            start_time = data[-1][0] + 1  # Add 1 millisecond to avoid duplication

            # Pause to avoid hitting API limits
            time.sleep(0.1)
        else:
            print(f"Error: Unable to fetch data. Status code {response.status_code}")
            break

    return all_data

# Fetch data
data = fetch_data(start_time, end_time, symbol, interval)

# Extract relevant columns: Open Time and Close Price
columns = ["Open Time", "Close"]
extracted_data = [[item[0], item[4]] for item in data]

# Create a DataFrame from the extracted data
df = pd.DataFrame(extracted_data, columns=columns)

# Convert timestamps to readable datetime format
df["Open Time"] = pd.to_datetime(df["Open Time"], unit='ms')
df["Close"] = df["Close"].astype(float)

# Display the first few rows of the DataFrame
print(df.head())

# Save the data to a CSV file (optional)
df.to_csv(f"ETHUSDC.csv", index=False)
