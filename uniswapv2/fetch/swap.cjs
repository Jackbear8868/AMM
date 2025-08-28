const { JsonRpcProvider, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// Initialize Infura provider
const provider = new JsonRpcProvider(
  `https://mainnet.infura.io/v3/5f960a322d10455197483e07b53297fa`
);

// Uniswap V2 ETH/USDC Pair contract address
const pairAddress = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc";

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
const startBlock = 10728353;
const endBlock = 21528671;
const maxBlocks = 1500;

// File to save CSV data
const csvFilePath = path.join(__dirname, "USDC_swap_events.csv");

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

// Sleep utility
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Get current timestamp for logging
const timestamp = () => new Date().toISOString().replace("T", " ").slice(0, 19);

// Main function with retry mechanism
(async () => {
  try {
    if (!fs.existsSync(csvFilePath)) {
      initializeCsvFile();
      console.log(`[${timestamp()}] ✅ CSV file initialized with headers.`);
    } else {
      console.log(`[${timestamp()}] ℹ️ CSV file already exists. Appending to existing file.`);
    }

    console.log(`[${timestamp()}] 🔍 Fetching Swap events from blocks ${startBlock} to ${endBlock}...`);

    let currentBlock = startBlock;

    while (currentBlock <= endBlock) {
      const toBlock = Math.min(currentBlock + maxBlocks - 1, endBlock);
      console.log(`[${timestamp()}] ➡️  Processing blocks ${currentBlock} → ${toBlock}`);

      const filter = pair.filters.Swap();
      let events;

      // Retry logic for queryFilter
      while (true) {
        try {
          events = await pair.queryFilter(filter, currentBlock, toBlock);
          break; // success
        } catch (err) {
          console.warn(`[${timestamp()}] ❗ Error fetching blocks ${currentBlock}-${toBlock}: ${err.message}`);
          console.log(`[${timestamp()}] ⏳ Retrying in 5 seconds...`);
          await sleep(5000);
        }
      }

      const processedData = events.map(event => ({
        blockNumber: event.blockNumber,
        amount0In: event.args.amount0In.toString(),
        amount1In: event.args.amount1In.toString(),
        amount0Out: event.args.amount0Out.toString(),
        amount1Out: event.args.amount1Out.toString()
      }));

      if (processedData.length > 0) {
        appendToCsvFile(processedData);
        console.log(`[${timestamp()}] ✔️  Appended ${processedData.length} records to CSV`);
      } else {
        console.log(`[${timestamp()}] – No swap events in this range.`);
      }

      currentBlock = toBlock + 1;
    }

    console.log(`[${timestamp()}] 🎉 All done. Data saved to ${csvFilePath}`);
  } catch (error) {
    console.error(`[${timestamp()}] ❌ Unexpected error in main process:`, error);
  }
})();
