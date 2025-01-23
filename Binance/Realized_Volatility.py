import pandas as pd
import numpy as np
import time

# Step 1: Load the minute-level price data
start_time = time.time()
df = pd.read_csv("ETHUSDC_1s.csv")

# Step 2: Calculate log returns
log_returns = np.log(df["Close"].values[1:] / df["Close"].values[:-1])

# Step 3: Define rolling window size (1440 minutes = 1 day)
window_size = 1440 * 60

# Step 4: Calculate rolling realized volatility using NumPy
realized_volatility = np.array([
    np.sqrt(np.sum(log_returns[i:i+window_size] ** 2))
    for i in range(len(log_returns) - window_size + 1)
])

# Step 5: Save results back to DataFrame
result_df = df.iloc[window_size:].copy()
result_df["Realized Volatility"] = realized_volatility

# Step 6: Save the result to a new CSV
result_df.to_csv("RV_1s.csv", index=False)

end_time = time.time()
print(f"Rolling realized volatility has been saved to 'RV_1m_optimized.csv'.")
print(f"Execution time: {end_time - start_time:.2f} seconds")
