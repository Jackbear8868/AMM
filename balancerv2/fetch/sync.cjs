const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// === 0. 手動設定 ===
const RPC_URL = "https://mainnet.infura.io/v3/5f960a322d10455197483e07b53297fa
";
const VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8";
const POOL_ID = "0x36be1e97ea98ab43b4debf92742517266f5731a3000200000000000000000466"; // ★ 把整個 32-bytes poolId 貼進來
const START_BLK = 21000000;          // 起始區塊
const END_BLK = 21528671;          // 結束區塊
const CHUNK = 5000;              // 每批抓多少區塊
const OUT_CSV = path.join(__dirname, "reserve.csv");

// === 1. Provider & 事件介面 ===
const provider = new ethers.providers.JsonRpcProvider(RPC_URL);
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
        name: "PoolBalanceChanged",
        type: "event"
    }
];
const iface = new ethers.utils.Interface(vaultAbi);
// const pbcTopic = iface.getEventTopic("PoolBalanceChanged");
// const poolIdTopic = ethers.utils.hexZeroPad(POOL_ID, 32);   // topic[1]

// === 2. 主流程 ===
(async () => {
    const rows = [];

    for (let from = START_BLK; from <= END_BLK; from += CHUNK) {
        const to = Math.min(from + CHUNK - 1, END_BLK);
        const logs = await provider.getLogs({
            address: VAULT,
            fromBlock: from,
            toBlock: to,
            topics: [pbcTopic, POOL_ID]   // 只抓這個 poolId 的 PBC
        });

        for (const log of logs) {
            const { args } = iface.parseLog(log);      // balances = 最新儲備
            rows.push({
                blockNumber: log.blockNumber,
                reserve0: args.balances[0].toString(),
                reserve1: args.balances[1].toString()
            });
        }
        process.stdout.write(`✓ ${from}-${to} (${rows.length} rows)\r`);
    }

    // === 3. 轉 CSV & 存檔 ===
    const csv = parse(rows, { fields: ["blockNumber", "reserve0", "reserve1"] });
    fs.writeFileSync(OUT_CSV, csv, "utf8");
    console.log(`\nDone – ${rows.length} rows → ${OUT_CSV}`);
})();
