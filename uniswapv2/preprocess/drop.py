import pandas as pd

# Define the file path and data types
file_path = "uniswap_v2.csv"
output_file = "drop.csv"
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

# Read the CSV file with specified dtypes
df = pd.read_csv(file_path, dtype=dtypes)

# Drop columns related to mint and burn
columns_to_drop = ["mint_amount0", "mint_amount1", "burn_amount0", "burn_amount1"]
df = df.drop(columns=columns_to_drop)

# Save the updated DataFrame to a new CSV file
df.to_csv(output_file, index=False)

print(f"Updated CSV saved as '{output_file}'.")
