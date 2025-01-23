const { providers, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// Initialize Infura provider
const provider = new providers.JsonRpcProvider(
  `https://mainnet.infura.io/v3/Your Infura API Key`
);

// Uniswap ETH/USDC Pair contract address
const pairAddress = "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc";

// Pair contract ABI with only getReserves
const pairAbi = [
  "function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)"
];

// Create contract instance
const pairContract = new Contract(pairAddress, pairAbi, provider);

// Block range
const startBlock = 18947061; // Start block
const endBlock = 21525890; // End block (example range)
const blockStep = 1; // Step size for iterating through blocks

// File to save CSV data
const csvFilePath = path.join(__dirname, "reserves.csv");

// Append data to the CSV file
const appendToCsvFile = (data) => {
  const fields = ["blockNumber", "reserve0", "reserve1"];
  const csvData = parse(data, { fields, header: false });
  fs.appendFileSync(csvFilePath, csvData + "\n");
};

// Main function
(async () => {
  try {
    // Initialize CSV file
    console.log(`Fetching reserves from blocks ${startBlock} to ${endBlock}...`);

    // Iterate through the specified block range
    for (let blockNumber = startBlock; blockNumber <= endBlock; blockNumber += blockStep) {
      try {
        // Fetch reserves at the specific block
        const reserves = await pairContract.getReserves({
          blockTag: blockNumber
        });

        // Process the result
        const reserveData = {
          blockNumber: blockNumber,
          reserve0: reserves.reserve0.toString(),
          reserve1: reserves.reserve1.toString(),
          blockTimestampLast: reserves.blockTimestampLast
        };

        console.log(`Block ${blockNumber}:`);

        // Append to CSV
        appendToCsvFile([reserveData]);
      } catch (error) {
        console.error(`Error fetching data for block ${blockNumber}:`, error);
      }
    }

    console.log(`All data saved to ${csvFilePath}`);
  } catch (error) {
    console.error("Error during execution:", error);
  }
})();
