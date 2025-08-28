const { JsonRpcProvider, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// Initialize Infura provider
const provider = new JsonRpcProvider(
    `https://mainnet.infura.io/v3/cd6bad5004284516a857f6d1c57af384`
);

// Uniswap V2 Pair contract address (Sync events)
const pairAddress = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc";

// ABI containing only the Sync event
const ProjectAbi = [
    {
        anonymous: false,
        inputs: [
            { indexed: false, name: "reserve0", type: "uint112" },
            { indexed: false, name: "reserve1", type: "uint112" }
        ],
        name: "Sync",
        type: "event"
    }
];

// Create contract instance
const pair = new Contract(pairAddress, ProjectAbi, provider);

// Block range
const startBlock = 10728353;
const endBlock = 21528671;
const maxBlocks = 1500;

// Output CSV path
const csvFilePath = path.join(__dirname, "USDC_sync_events.csv");

// Timestamp helper
const timestamp = () => new Date().toISOString().replace("T", " ").slice(0, 19);

// Initialize CSV file with headers
const initializeCsvFile = () => {
    const fields = ["blockNumber", "reserve0", "reserve1"];
    const csvHeader = fields.join(",") + "\n";
    fs.writeFileSync(csvFilePath, csvHeader);
};

// Append data to CSV
const appendToCsvFile = (data) => {
    const fields = ["blockNumber", "reserve0", "reserve1"];
    const csvData = parse(data, { fields, header: false });
    fs.appendFileSync(csvFilePath, csvData + "\n");
};

// Sleep function
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Main process
(async () => {
    try {
        if (!fs.existsSync(csvFilePath)) {
            initializeCsvFile();
            console.log(`[${timestamp()}] ✅ CSV file initialized with headers.`);
        } else {
            console.log(`[${timestamp()}] ℹ️ CSV file already exists. Appending to existing file.`);
        }

        console.log(`[${timestamp()}] 🔍 Fetching Sync events from blocks ${startBlock} to ${endBlock}...`);

        let currentBlock = startBlock;

        while (currentBlock <= endBlock) {
            const toBlock = Math.min(currentBlock + maxBlocks - 1, endBlock);
            console.log(`[${timestamp()}] ➡️  Processing blocks ${currentBlock} → ${toBlock}`);

            const filter = pair.filters.Sync();
            let events;

            // Retry until success
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
                reserve0: event.args.reserve0.toString(),
                reserve1: event.args.reserve1.toString()
            }));

            if (processedData.length > 0) {
                appendToCsvFile(processedData);
                console.log(`[${timestamp()}] ✔️  Appended ${processedData.length} records to CSV`);
            } else {
                console.log(`[${timestamp()}] – No Sync events in this range.`);
            }

            currentBlock = toBlock + 1;
        }

        console.log(`[${timestamp()}] 🎉 All done. Data saved to ${csvFilePath}`);
    } catch (error) {
        console.error(`[${timestamp()}] ❌ Unexpected error in main process:`, error);
    }
})();
