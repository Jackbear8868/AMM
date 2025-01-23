import csv
from dune_client.client import DuneClient
from datetime import datetime, timezone

# Initialize Dune Client
dune = DuneClient("Your Dune Api key", request_timeout=1000000)

# Fetch the latest query result
query_result = dune.get_latest_result(4610627)

# Extract rows and column names from the result
rows = query_result.result.rows  # List of dictionaries containing data
column_names = query_result.result.metadata.column_names  # Column headers

# Define output CSV file
output_file = "timestamp.csv"

# Write the data to a CSV file
with open(output_file, mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=column_names)
    writer.writeheader()  # Write column headers
    
    # Process rows to update the 'Timestamp' column
    for row in rows:
        if "Timestamp" in row:
            # Convert the timestamp to a readable format
            row["Timestamp"] = datetime.fromtimestamp(row["Timestamp"], timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow(row)  # Write the modified row

print(f"CSV file has been created with updated 'Timestamp' column: {output_file}")
