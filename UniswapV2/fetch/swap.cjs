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

// ABI containing only the Swap event
const ProjectAbi = [
  {
    anonymous: false,
    inputs: [
      { indexed: true, name: "sender", type: "address" },
      { indexed: false, name: "amount0In", type: "uint" },
      { indexed: false, name: "amount1In", type: "uint" },
      { indexed: false, name: "amount0Out", type: "uint" },
      { indexed: false, name: "amount1Out", type: "uint" },
      { indexed: true, name: "to", type: "address" }
    ],
    name: "Swap",
    type: "event"
  }
];

// Create contract instance
const pair = new Contract(pairAddress, ProjectAbi, provider);

// Block range
const startBlock = 18908894; // Start block
const endBlock = 21528671; // End block
const maxBlocks = 5000; // Limit block range to 1000 blocks
// 21528671
// File to save CSV data
const csvFilePath = path.join(__dirname, "swap_events.csv");

// Initialize CSV file with headers
const initializeCsvFile = () => {
  const fields = ["blockNumber", "amount0In", "amount1In", "amount0Out", "amount1Out"];
  const csvHeader = fields.join(",") + "\n";
  fs.writeFileSync(csvFilePath, csvHeader);
};

// Append data to the CSV file
const appendToCsvFile = (data) => {
  const fields = ["blockNumber", "amount0In", "amount1In", "amount0Out", "amount1Out"];
  const csvData = parse(data, { fields, header: false });
  fs.appendFileSync(csvFilePath, csvData + "\n");
};

// Main function
(async () => {
  try {
    // Initialize CSV file
    initializeCsvFile();

    console.log(`Fetching Swap events from blocks ${startBlock} to ${endBlock}...`);

    // Iterate through block ranges
    let currentBlock = startBlock;

    while (currentBlock < endBlock) {
      const toBlock = Math.min(currentBlock + maxBlocks - 1, endBlock);

      console.log(`Fetching Swap events from blocks ${currentBlock} to ${toBlock}...`);

      const filter = pair.filters.Swap();
      const events = await pair.queryFilter(filter, currentBlock, toBlock);

      console.log(`Fetched ${events.length} Swap events from blocks ${currentBlock} to ${toBlock}`);

      // Process and save events to CSV
      const processedData = events.map(event => ({
        blockNumber: event.blockNumber,
        amount0In: event.args.amount0In.toString(),
        amount1In: event.args.amount1In.toString(),
        amount0Out: event.args.amount0Out.toString(),
        amount1Out: event.args.amount1Out.toString()
      }));

      appendToCsvFile(processedData);

      // Move to the next block range
      currentBlock = toBlock + 1;
    }

    console.log(`All data saved to ${csvFilePath}`);
  } catch (error) {
    console.error("Error fetching Swap events:", error);
  }
})();
