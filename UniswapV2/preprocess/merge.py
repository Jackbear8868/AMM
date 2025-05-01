import pandas as pd

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
    # Add other columns here with specific data types if necessary
}


# Load the two CSV files into DataFrames
df1 = pd.read_csv("timestamp.csv", low_memory=False, dtype=dtypes)
df2 = pd.read_csv("merge.csv", low_memory=False, dtype=dtypes)

# Merge the two DataFrames on the 'blockNumber' column using an outer join
merged_df = pd.merge(df1, df2, on="blockNumber", how="outer")

# Sort the DataFrame by 'blockNumber'
merged_df = merged_df.sort_values(by="blockNumber")

# Save the merged DataFrame to a new CSV file
merged_df.to_csv("merge.csv", index=False)

print("Merged CSV saved as 'merge.csv'")
