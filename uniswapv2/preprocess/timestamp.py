import pandas as pd
from datetime import datetime, timedelta

# File paths
input_file = "timestamp.csv"
output_file = "test.csv"

dtypes = {
    "burn_amount0": "string",
    "burn_amount1": "string",
    "mint_amount0": "string",
    "mint_amount1": "string",
    "reserve0": "string",
    "reserve1": "string",
    "amount0In": "string",
    "amount1In": "string",
    "amount0Out": "string",
    "amount1Out": "string",
}

# Initial values
start_block = 18908894
start_timestamp = "2023-12-31 11:59:59"  # Starting timestamp
average_block_time = 12.09992925000  # Average block generation period in seconds

# Read the CSV file
df = pd.read_csv(input_file, low_memory=False, dtype=dtypes)

# Ensure the CSV has a 'blockNumber' column
if "blockNumber" not in df.columns:
    raise ValueError("The CSV must contain a 'blockNumber' column.")

# Sort by blockNumber to ensure proper calculation
df = df.sort_values(by="blockNumber").reset_index(drop=True)

# Calculate the timestamp for each block
current_time = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S")
timestamps = []

for block in df["blockNumber"]:
    time_difference = (block - start_block) * average_block_time
    adjusted_time = current_time + timedelta(seconds=time_difference)
    timestamps.append(adjusted_time.strftime("%Y-%m-%d %H:%M:%S"))

# Replace or add the timestamp column
df["Timestamp"] = timestamps
df.drop(columns=['timestamp'], inplace=True)
# Save the updated DataFrame to a new CSV
df.to_csv(output_file, index=False)

print(f"CSV with updated timestamps saved as '{output_file}'.")
