#!/usr/bin/env node
require("dotenv").config();
const { JsonRpcProvider, Contract } = require("ethers");
const fs = require("fs");
const path = require("path");
const { parse } = require("json2csv");

// ==== 1. 手動設定參數 ====
const RPC_URL = `https://bsc-mainnet.infura.io/v3/5f960a322d10455197483e07b53297fa`;
const pairAddress = "0x0eD7e52944161450477ee417DE9Cd3a859b14fD0";  // 手動填入你要的 Pool 地址
const startBlock = 6810706;    // 手動填起始區塊  6810706 
const endBlock = 45369482;    // 手動填結束區塊（含）45369482
const step = 10000;        // 每批查詢區塊數

// ==== 2. ABI & 合約 ====
const provider = new JsonRpcProvider(RPC_URL);
const PAIR_ABI = [
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
const pair = new Contract(pairAddress, PAIR_ABI, provider);
const csvPath = path.resolve(__dirname, "CAKE_WBNB_swaps.csv");

// ==== 3. CSV 工具函式 ====
function initCsv() {
  const header = ["blockNumber", "amount0In", "amount1In", "amount0Out", "amount1Out"].join(",") + "\n";
  fs.writeFileSync(csvPath, header);
}

function appendCsv(rows) {
  const csv = parse(rows, {
    fields: ["blockNumber", "amount0In", "amount1In", "amount0Out", "amount1Out"],
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
    console.log("✅ CSV 檔案已初始化");
  } else {
    console.log("ℹ️ CSV 已存在，將追加資料");
  }

  console.log(`🔍 抓取 Swap 事件：blocks ${startBlock} → ${endBlock} (step=${step})`);
  const filter = pair.filters.Swap();

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
        console.log("   即將在 5 秒後重試...");
        await sleep(5000);
      }
    }

    // 處理抓到的結果（即使 logs.length === 0 也算成功）
    const data = logs.map(e => ({
      blockNumber: e.blockNumber,
      amount0In: e.args.amount0In.toString(),
      amount1In: e.args.amount1In.toString(),
      amount0Out: e.args.amount0Out.toString(),
      amount1Out: e.args.amount1Out.toString(),
    }));

    if (data.length) {
      appendCsv(data);
      console.log(`    ✔ 新增 ${data.length} 筆資料`);
    } else {
      console.log("    – 本批無事件");
    }

    cursor = toBlock + 1;
  }

  console.log(`🎉 全部完成，結果已儲存至 ${csvPath}`);
})();
