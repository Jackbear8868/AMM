import pandas as pd
import matplotlib.pyplot as plt

# Define file path
file_path = "ETHUSDC_1m.csv"

# Read the CSV file with all columns as strings
df = pd.read_csv(file_path, dtype=str)

df['Timestamp'] = pd.to_datetime(df['Timestamp'])  # Convert to datetime
# Convert specific columns to integers
columns_to_convert = ["ETH_price"]

for column in columns_to_convert:
    df[column] = df[column].apply(lambda x: float(x) if pd.notnull(x) else 0)

# Drop rows with missing or invalid values
df = df.dropna(subset=['Timestamp', 'ETH_price'])

# Plot the graph
plt.figure(figsize=(10, 6))
plt.plot(df['Timestamp'], df['ETH_price'], label="ETH Price")
plt.xlabel("Timestamp", fontsize=12)
plt.ylabel("ETH Price (USDC)", fontsize=12)
plt.title("ETH Price Over Time", fontsize=14)
plt.grid(True)
plt.legend()
plt.tight_layout()

# Save the graph as an image (optional)
plt.savefig("eth_price_graph.png")

print("Converted CSV saved as 'converted_file.csv'.")
