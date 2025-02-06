import pandas as pd

# File paths
input_file = "./merge.csv"
output_file = "./uniswap_v2.csv"

# Specify the start row and chunk size
start_row = 1  # Start processing from this row
chunksize = 3000  # Number of rows per chunk

previous_row = pd.read_csv(input_file, skiprows=range(1, start_row - 1), nrows=1, dtype="string")

# Process the file in chunks starting from the specific row
for chunk in pd.read_csv(input_file, chunksize=chunksize, skiprows=range(1, start_row-1), dtype="string"):

    chunk = pd.concat([previous_row, chunk], ignore_index=True)

    # Calculate reserve0 and reserve1 iteratively
    for i in range(1, len(chunk)):
        chunk.loc[i, "reserve0"] = str(
            int(chunk.loc[i - 1, "reserve0"])  # reserve0(t-1)
            + int(chunk.loc[i, "mint_amount0"])
            - int(chunk.loc[i, "burn_amount0"])
            + int(chunk.loc[i, "amount0In"])
            - int(chunk.loc[i, "amount0Out"])
        )
        chunk.loc[i, "reserve1"] = str(
            int(chunk.loc[i - 1, "reserve1"])  # reserve1(t-1)
            + int(chunk.loc[i, "mint_amount1"])
            - int(chunk.loc[i, "burn_amount1"])
            + int(chunk.loc[i, "amount1In"])
            - int(chunk.loc[i, "amount1Out"])
        )

        chunk.loc[i, "ETH_price"] = str(round(int(chunk.loc[i, "reserve0"]) * 10**12 / int(chunk.loc[i, "reserve1"]), 2))

    # Save the last row of this chunk for the next iteration
    previous_row = chunk.iloc[[-1]]  # Preserve the last row for continuity

    # Drop the last row before saving the chunk (it will be processed in the next chunk)
    chunk = chunk.iloc[:-1]

    # Append processed chunk to the output file
    chunk.to_csv(output_file, mode="a", index=False, header=False)

# Save the final previous row (last row of the last chunk)
previous_row.to_csv(output_file, mode="a", index=False, header=False)

print(f"Processing completed. Processed file saved to '{output_file}'.")
