import pandas as pd

# File paths
block_file = "ETHUSDC_12s.csv"  # Contains blockNumber and timestamp
price_file = "ETHUSDC_1s.csv"  # Contains price and timestamp
output_file = "ETHUSDC.csv"

# Read the two CSV files
blocks_df = pd.read_csv(block_file)
blocks_df.drop(columns=['ETH_price'], inplace=True)
prices_df = pd.read_csv(price_file)

# Ensure the timestamp columns are in datetime format
blocks_df['Timestamp'] = pd.to_datetime(blocks_df['Timestamp'])
prices_df['Timestamp'] = pd.to_datetime(prices_df['Timestamp'])

# Merge the DataFrames on the timestamp column
merged_df = pd.merge(blocks_df, prices_df, on="Timestamp", how="inner")

# Save the merged data to a new CSV file
merged_df.to_csv(output_file, index=False)

print(f"Merged data saved as '{output_file}'.")
