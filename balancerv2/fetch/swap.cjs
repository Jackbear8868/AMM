const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// 以太坊 RPC Provider (Infura)
const provider = new ethers.providers.JsonRpcProvider(
  `https://mainnet.infura.io/v3/5f960a322d10455197483e07b53297fa
`
);

// Vault 合約地址（固定）
const vaultAddress = "0xBA12222222228d8Ba445958a75a0704d566BF2C8";

// Vault ABI（只需要 Swap 事件）
const vaultAbi = [
  {
    anonymous: false,
    inputs: [
      { indexed: true, internalType: "bytes32", name: "poolId", type: "bytes32" },
      { indexed: true, internalType: "address", name: "tokenIn", type: "address" },
      { indexed: true, internalType: "address", name: "tokenOut", type: "address" },
      { indexed: false, internalType: "uint256", name: "amountIn", type: "uint256" },
      { indexed: false, internalType: "uint256", name: "amountOut", type: "uint256" }
    ],
    name: "Swap",
    type: "event"
  }
];

// 👉 你想要過濾的 Pool ID（bytes32 格式）
const targetPoolId = "0x92762b42a06dcdddc5b7362cfb01e631c4d44b40000200000000000000000182".toLowerCase();

const tokenAddressToName = {
  "0x44108f0223a3c3028f5fe7aec7f9bb2e66bef82f": "ACX",
  "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0": "wstETH",
  "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
  "0xaf5191b0de278c7286d6c7cc6ab6bb8a73ba2cd6": "STG",
  "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
  "0xdef1ca1fb7fbcdc777520aa7f396b4e015f497ab": "COW",
  "0x6810e776880c02933d47db1b9fc05908e5386b96": "GNO",
  "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": "WBTC",
  "0x68037790a0229e9ce6eaa8a99ea92964106c4703": "PAR",
};

// Pool 對應的 token0/token1（手動定義）
const tokenPair = {
  "ACX/wstETH": ["ACX", "wstETH"],
  "USDC/STG": ["USDC", "STG"],
  "WETH/COW": ["WETH", "COW"],
  "GNO/COW": ["GNO", "COW"],
  "WBTC/WETH": ["WBTC", "WETH"],
  "PAR/WETH": ["PAR", "WETH"]
};

const poolName = "GNO/COW";

// 區塊範圍
const startBlock = 14475132;
const endBlock = 21528671;
const maxBlocks = 10000;

// 匯出 CSV 的路徑
const csvFilePath = path.join(__dirname, "GNO_COW_swap_events.csv");

// 初始化 CSV
const initializeCsvFile = () => {
  const fields = ["blockNumber", "amount0In", "amount1In", "amount0Out", "amount1Out"];
  const csvHeader = fields.join(",") + "\n";
  fs.writeFileSync(csvFilePath, csvHeader);
};

// 寫入 CSV
const appendToCsvFile = (data) => {
  const fields = ["blockNumber", "amount0In", "amount1In", "amount0Out", "amount1Out"];
  const csvData = parse(data, { fields, header: false });
  fs.appendFileSync(csvFilePath, csvData + "\n");
};

function parseSwapEvents(logs, iface, tokenAddressToName, tokens) {
  const [token0, token1] = tokens;

  return logs.map((log) => {
    const parsed = iface.parseLog(log);
    const tokenInAddr = parsed.args.tokenIn.toLowerCase();
    const tokenOutAddr = parsed.args.tokenOut.toLowerCase();

    const nameIn = tokenAddressToName[tokenInAddr] || tokenInAddr;
    const nameOut = tokenAddressToName[tokenOutAddr] || tokenOutAddr;

    const amountIn = parsed.args.amountIn.toString();
    const amountOut = parsed.args.amountOut.toString();

    let amount0In = "0", amount0Out = "0", amount1In = "0", amount1Out = "0";

    if (nameIn === token0) amount0In = amountIn;
    if (nameOut === token0) amount0Out = amountOut;
    if (nameIn === token1) amount1In = amountIn;
    if (nameOut === token1) amount1Out = amountOut;

    return {
      blockNumber: log.blockNumber,
      amount0In,
      amount1In,
      amount0Out,
      amount1Out
    };
  });
}




// 主程式
(async () => {
  try {
    // 準備 ABI interface
    const iface = new ethers.utils.Interface(vaultAbi);
    const topic0 = iface.getEventTopic("Swap");

    // 建立 CSV
    if (!fs.existsSync(csvFilePath)) {
      initializeCsvFile();
      console.log("CSV initialized.");
    }

    let currentBlock = startBlock;

    while (currentBlock <= endBlock) {
      const toBlock = Math.min(currentBlock + maxBlocks - 1, endBlock);
      console.log(`📦 Fetching from blocks ${currentBlock} → ${toBlock}...`);

      const filter = {
        address: vaultAddress,
        topics: [
          topic0,
          targetPoolId
        ],
        fromBlock: currentBlock,
        toBlock: toBlock
      };

      const logs = await provider.getLogs(filter);
      console.log(`🔍 Found ${logs.length} logs`);

      if (!tokenPair[poolName]) {
        throw new Error(`❌ Token pair not found for pool: ${poolName}`);
      }
      const events = parseSwapEvents(logs, iface, tokenAddressToName, tokenPair[poolName]);

      if (events.length > 0) {
        appendToCsvFile(events);
        console.log(`✅ Appended ${events.length} events`);
      }

      currentBlock = toBlock + 1;
    }

    console.log(`🎉 Done! Events saved to ${csvFilePath}`);
  } catch (err) {
    console.error("❌ Error fetching logs:", err);
  }
})();
