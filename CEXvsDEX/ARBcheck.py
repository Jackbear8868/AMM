import pandas as pd
import matplotlib.pyplot as plt

# Load the merged CSV file
merged_csv_file = "Merged_ETH_Price_Comparison.csv"  # Make sure this file exists
df = pd.read_csv(merged_csv_file, low_memory=False)

# Ensure 'Timestamp' is parsed as datetime
df["Timestamp"] = pd.to_datetime(df["Timestamp"])

# **Calculate the non-arbitrage range**
df["Uniswap_Upper_Bound"] = df["Uniswap_ETH_price"] * 1.003
df["Uniswap_Lower_Bound"] = df["Uniswap_ETH_price"] * 0.997

# **Identify arbitrage opportunities**
df["Arbitrage_Opportunity"] = (
    (df["Binance_ETH_price"] > df["Uniswap_Upper_Bound"]) |  # Binance price too high
    (df["Binance_ETH_price"] < df["Uniswap_Lower_Bound"])    # Binance price too low
)

# Save the data with arbitrage opportunities
df.to_csv("Arbitrage_Analysis.csv", index=False)

# **Plot the data**
plt.figure(figsize=(19.2, 10.8), dpi=300)

# **Plot Binance ETH price**
plt.plot(df["Timestamp"], df["Binance_ETH_price"], label="Binance Price", color="orange", linestyle="--")

# **Plot Uniswap ETH price**
plt.plot(df["Timestamp"], df["Uniswap_ETH_price"], label="Uniswap v2 Price", color="blue")

# **Plot Non-Arbitrage Range**
plt.fill_between(df["Timestamp"], df["Uniswap_Lower_Bound"], df["Uniswap_Upper_Bound"], 
                 color='green', alpha=0.2, label="Non-Arbitrage Range")

# **Highlight Arbitrage Opportunities**
arbitrage_mask = df["Arbitrage_Opportunity"]
plt.scatter(df["Timestamp"][arbitrage_mask], df["Binance_ETH_price"][arbitrage_mask], 
            color="red", label="Arbitrage Opportunities", marker="o", s=10)

# **Labels, title, and legend**
plt.xlabel("Timestamp", fontsize=12)
plt.ylabel("ETH Price", fontsize=12)
plt.title("Binance vs Uniswap v2: Arbitrage Opportunities", fontsize=14)
plt.legend()
plt.grid(True)

# **Save the figure in high resolution**
plt.savefig("Binance_vs_Uniswap_Arbitrage.png", dpi=300, bbox_inches="tight")
