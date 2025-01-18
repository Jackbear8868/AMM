const { providers, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// Initialize Infura provider
const provider = new providers.JsonRpcProvider(
  `https://mainnet.infura.io/v3/10311d634e48456eb1a692b8952d47eb`
);

// Uniswap ETH/USDC Pair contract address
const pairAddress = "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc";

// ABI containing only the mint event
const ProjectAbi = [
  {
    anonymous: false,
    inputs: [
      { indexed: true, name: "sender", type: "address" },
      { indexed: false, name: "amount0", type: "uint" },
      { indexed: false, name: "amount1", type: "uint" },
    ],
    name: "Mint",
    type: "event"
  }
];

// Create contract instance
const pair = new Contract(pairAddress, ProjectAbi, provider);

// Block range
const startBlock = 18908895; // Start block
const endBlock = 21525890; // End block
const maxBlocks = 5000; // Limit block range to 1000 blocks

// File to save CSV data
const csvFilePath = path.join(__dirname, "mint_events.csv");

// Initialize CSV file with headers
const initializeCsvFile = () => {
  const fields = ["blockNumber", "amount0", "amount1"];
  const csvHeader = fields.join(",") + "\n";
  fs.writeFileSync(csvFilePath, csvHeader);
};

// Append data to the CSV file
const appendToCsvFile = (data) => {
  if (data.length === 0) return; // Skip appending if no data
  const fields = ["blockNumber", "amount0", "amount1"];
  const csvData = parse(data, { fields, header: false });
  fs.appendFileSync(csvFilePath, csvData + "\n");
};

// Main function
(async () => {
  try {
    // Initialize CSV file
    initializeCsvFile();

    console.log(`Fetching mint events from blocks ${startBlock} to ${endBlock}...`);

    // Iterate through block ranges
    let currentBlock = startBlock;

    while (currentBlock < endBlock) {
      const toBlock = Math.min(currentBlock + maxBlocks - 1, endBlock);

      console.log(`Fetching mint events from blocks ${currentBlock} to ${toBlock}...`);

      const filter = pair.filters.Mint();
      const events = await pair.queryFilter(filter, currentBlock, toBlock);

      console.log(`Fetched ${events.length} Mint events from blocks ${currentBlock} to ${toBlock}`);

      // Process and save events to CSV
      const processedData = events.map(event => ({
        blockNumber: event.blockNumber,
        amount0: event.args.amount0.toString(),
        amount1: event.args.amount1.toString(),
      }));

      appendToCsvFile(processedData);

      // Move to the next block range
      currentBlock = toBlock + 1;
    }

    console.log(`All data saved to ${csvFilePath}`);
  } catch (error) {
    console.error("Error fetching Mint events:", error);
  }
})();
