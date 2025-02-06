import pandas as pd

# Define file paths
input_file = "ETHUSDC_1s.csv"
output_file = "ETHUSDC_12s.csv"

# Read the CSV file
df = pd.read_csv(input_file)

# Ensure the datetime column is parsed as datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Resample to 15-second intervals by selecting every 15th row
df_15s = df.iloc[11::12].reset_index(drop=True)

# Save the new DataFrame to a CSV file
df_15s.to_csv(output_file, index=False)

print(f"CSV with 15-second intervals saved as '{output_file}'.")
