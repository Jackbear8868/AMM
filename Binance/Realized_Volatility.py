import pandas as pd
import numpy as np
import time

start_time = time.time()  # Start the timer

# Step 1: Load the minute-level price data
df = pd.read_csv("ETHUSDC_1m.csv")

# Step 3: Calculate log returns
df["Log Return"] = np.log(df["Close"] / df["Close"].shift(1))

# Step 4: Define a rolling window size (1440 minutes = 1 day)
window_size = 1440

# Step 5: Calculate rolling realized volatility
def rolling_realized_volatility(log_returns):
    return np.sqrt(np.sum(log_returns ** 2))

# Apply rolling window calculation
df["Realized Volatility"] = (
    df["Log Return"]
    .rolling(window=window_size)
    .apply(rolling_realized_volatility, raw=False)
)

# Step 6: Drop NaN values (caused by the rolling window) and save results
df = df.dropna()
df.drop(columns=["Log Return"], inplace=True)
df.to_csv("RV_1m.csv", index=False)

end_time = time.time()  # End the timer
execution_time = end_time - start_time  # Calculate total time

print(f"Rolling realized volatility has been saved to 'RV_1m.csv'.")
print(f"Execution time: {execution_time:.2f} seconds")
