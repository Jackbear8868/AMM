#!/usr/bin/env node
require("dotenv").config();
const { JsonRpcProvider, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// ==== 1. 手動設定參數 ====
const RPC_URL = `https://bsc-mainnet.infura.io/v3/5f960a322d10455197483e07b53297fa`;
const pairAddress = "0x16b9a82891338f9bA80E2D6970FddA79D1eb0daE";  // 你的 Pool 地址
const startBlock = 45360000;     // 起始區塊
const endBlock = 45369482;    // 結束區塊（含）
const step = 10000;        // 每批查詢區塊數

// ==== 2. ABI & 合約實例 ====
const provider = new JsonRpcProvider(RPC_URL);
const PAIR_ABI = [
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
const pair = new Contract(pairAddress, PAIR_ABI, provider);
const csvPath = path.resolve(__dirname, "tmp_USDT_WBNB_syncs.csv");

// ==== 3. CSV 工具函式 ====
function initCsv() {
    const header = ["blockNumber", "reserve0", "reserve1"].join(",") + "\n";
    fs.writeFileSync(csvPath, header);
}

function appendCsv(rows) {
    const csv = parse(rows, {
        fields: ["blockNumber", "reserve0", "reserve1"],
        header: false
    }) + "\n";
    fs.appendFileSync(csvPath, csv);
}

// ==== 4. Sleep 函式 ====
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==== 5. 主程序：帶重試的 queryFilter ====
(async () => {
    if (!fs.existsSync(csvPath)) {
        initCsv();
        console.log("✅ CSV 已初始化");
    } else {
        console.log("ℹ️ CSV 已存在，將追加資料");
    }

    console.log(`🔍 抓取 Sync 事件：blocks ${startBlock} → ${endBlock} (step=${step})`);
    const filter = pair.filters.Sync();

    let cursor = startBlock;
    while (cursor <= endBlock) {
        const toBlock = Math.min(cursor + step - 1, endBlock);
        console.log(`  • 區塊 ${cursor} → ${toBlock}`);

        // 帶重試的抓取
        let logs;
        while (true) {
            try {
                logs = await pair.queryFilter(filter, cursor, toBlock);
                break;  // 成功就跳出重試迴圈
            } catch (err) {
                console.warn(`❗️ 抓取區塊 ${cursor}-${toBlock} 時出錯：${err.message}`);
                console.log("   等待 5 秒後重試...");
                await sleep(5000);
            }
        }

        // 處理抓到的結果
        const data = logs.map(e => ({
            blockNumber: e.blockNumber,
            reserve0: e.args.reserve0.toString(),
            reserve1: e.args.reserve1.toString(),
        }));

        if (data.length) {
            appendCsv(data);
            console.log(`    ✔ 新增 ${data.length} 筆資料`);
        } else {
            console.log("    – 本批無事件");
        }

        cursor = toBlock + 1;
    }

    console.log(`🎉 完成，結果儲存在 ${csvPath}`);
})();
