const { providers, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// Initialize Infura provider
const provider = new providers.JsonRpcProvider(
    `https://mainnet.infura.io/v3/10311d634e48456eb1a692b8952d47eb`
);

// Uniswap V2 ETH/USDC Pair contract address
const pairAddress = "0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc";

// ABI containing only the Swap event
const ProjectAbi = [
    {
        anonymous: false,
        inputs: [
            { indexed: false, name: "reserve0", type: "uint112" },
            { indexed: false, name: "reserve1", type: "uint112" },
        ],
        name: "Sync",
        type: "event"
    }
];

// Create contract instance
const pair = new Contract(pairAddress, ProjectAbi, provider);

// Block range
const startBlock = 21520000; // Start block 10728353 14945353
const endBlock = 21528671; // End block
const maxBlocks = 3500; // Limit block range to 5000 blocks
// 21528671
// File to save CSV data
const csvFilePath = path.join(__dirname, "tmp_sync_events.csv");

// Initialize CSV file with headers
const initializeCsvFile = () => {
    const fields = ["blockNumber", "reserve0", "reserve1"];
    const csvHeader = fields.join(",") + "\n";
    fs.writeFileSync(csvFilePath, csvHeader);
};

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
        if (!fs.existsSync(csvFilePath)) {
            initializeCsvFile();
            console.log("CSV file initialized with headers.");
        } else {
            console.log("CSV file already exists. Appending to existing file.");
        }

        console.log(`Fetching Swap events from blocks ${startBlock} to ${endBlock}...`);

        // Iterate through block ranges
        let currentBlock = startBlock;

        while (currentBlock < endBlock) {
            const toBlock = Math.min(currentBlock + maxBlocks - 1, endBlock);

            console.log(`Fetching Swap events from blocks ${currentBlock} to ${toBlock}...`);

            const filter = pair.filters.Sync();
            const events = await pair.queryFilter(filter, currentBlock, toBlock);

            console.log(`Fetched ${events.length} Swap events from blocks ${currentBlock} to ${toBlock}`);

            // Process and save events to CSV
            const processedData = events.map(event => ({
                blockNumber: event.blockNumber,
                reserve0: event.args.reserve0.toString(),
                reserve1: event.args.reserve1.toString(),
            }));

            if (processedData.length > 0) {
                appendToCsvFile(processedData);
                console.log(`Appended ${processedData.length} records to CSV.`);
            } else {
                console.log("No swap events found in this block range. Skipping write.");
            }

            // Move to the next block range
            currentBlock = toBlock + 1;
        }

        console.log(`All data saved to ${csvFilePath}`);
    } catch (error) {
        console.error("Error fetching Swap events:", error);
    }
})();
