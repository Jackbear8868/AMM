import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV files
high_freq_csv = pd.read_csv("./Binance/datas/ETHUSDC_1s.csv", low_memory=False)  # High-frequency data
low_freq_csv = pd.read_csv("./UniswapV2/datas/drop.csv", low_memory=False)  # Low-frequency data

# Ensure 'Timestamp' is parsed as datetime
high_freq_csv['Timestamp'] = pd.to_datetime(high_freq_csv['Timestamp'])
low_freq_csv['Timestamp'] = pd.to_datetime(low_freq_csv['Timestamp'])

# Remove duplicate timestamps
high_freq_csv = high_freq_csv.drop_duplicates(subset=['Timestamp']).sort_values(by="Timestamp")
low_freq_csv = low_freq_csv.drop_duplicates(subset=['Timestamp']).sort_values(by="Timestamp")

# Set 'Timestamp' as the index
high_freq_csv.set_index('Timestamp', inplace=True)
low_freq_csv.set_index('Timestamp', inplace=True)

# Forward-fill Uniswap's low-frequency prices to match Binance's high-frequency timestamps
low_freq_resampled = low_freq_csv.reindex(high_freq_csv.index).ffill()

# Merge both datasets into a new DataFrame
merged_df = high_freq_csv.copy()
merged_df["Uniswap_ETH_price"] = low_freq_resampled["Uniswap_ETH_price"]

# **Convert price columns to float**
merged_df["Uniswap_ETH_price"] = pd.to_numeric(merged_df["Uniswap_ETH_price"], errors="coerce")
merged_df["Binance_ETH_price"] = pd.to_numeric(merged_df["Binance_ETH_price"], errors="coerce")

# **Drop NaN values** (important for proper plotting)
merged_df.dropna(subset=["Uniswap_ETH_price", "Binance_ETH_price"], inplace=True)

# Save the cleaned merged data
merged_df.to_csv("Merged_ETH_Price_Comparison.csv")

# **Plot both datasets**
plt.figure(figsize=(19.2, 10.8), dpi=300)

# Plot Binance ETH price
plt.plot(merged_df.index, merged_df['Binance_ETH_price'], label='Binance', color='orange', linestyle='--')

# Plot Uniswap ETH price (after forward-filling)
plt.plot(merged_df.index, merged_df['Uniswap_ETH_price'], label='Uniswap v2', color='blue')

# Add labels, title, and legend
plt.xlabel("Timestamp", fontsize=12)
plt.ylabel("ETH Price", fontsize=12)
plt.title("Binance vs Uniswap v2 ETH Prices", fontsize=14)
plt.legend()
plt.grid(True)

# Save and show the plot
plt.savefig("Binance_vs_Uniswap_v2_HD.png", dpi=300, bbox_inches="tight")
