import pandas as pd
import numpy as np
pd.set_option("display.float_format", "{:.6f}".format)

# ============================================================
# 0‧ 基本參數（修改這裡就好）
# ============================================================
SWAP_FILE  = "USDT_WBNB_swaps.csv"
SYNC_FILE  = "USDT_WBNB_syncs.csv"
OUTPUT_CSV = "USDT_WBNB_token0.csv"

# ★ token0 = USD（USDC、USDT…）、token1 = ETH（WETH、WBTC 就改成 8）
DEC0 = 6       # token0 decimals
DEC1 = 18      # token1 decimals

FEE_RATE   = 0.003
BLOCK_INTERVAL_SECONDS = 12               # 1 block ≈ 12 s (ETH mainnet)

# ============================================================
# 1‧ 讀檔
# ============================================================
swaps_df = pd.read_csv(
    SWAP_FILE,
    converters={"blockNumber": int,
                "amount0In": int, "amount1In": int,
                "amount0Out": int, "amount1Out": int})

syncs_df = pd.read_csv(
    SYNC_FILE,
    converters={"blockNumber": int,
                "reserve0": int, "reserve1": int})

# ============================================================
# 2‧ reserves → 每區塊最後一次 Sync
# ============================================================
reserves_raw = (syncs_df.sort_values("blockNumber")
                          .groupby("blockNumber", as_index=False)
                          .last())

first_blk = int(reserves_raw["blockNumber"].min())
last_blk  = int(reserves_raw["blockNumber"].max())
all_blocks = pd.DataFrame({
    "blockNumber": np.arange(first_blk, last_blk + 1, dtype="int64")
})

# 把缺洞補進來，reserve0/1 用前值 ffill
reserves = (all_blocks
              .merge(reserves_raw, on="blockNumber", how="left")
              .ffill())                # price、pool_value 之後才算，這裡先填 reserve

# 2-1：人類單位、2-2：mid-price
reserves["r0_h"] = reserves["reserve0"] / 10**DEC0
reserves["r1_h"] = reserves["reserve1"] / 10**DEC1
reserves["price"] = reserves["r0_h"] / reserves["r1_h"]
reserves["price"] = reserves["price"].astype(np.float64)

# 2-3：pool_value
reserves["pool_value"] = reserves["r0_h"] + reserves["r1_h"] * reserves["price"]

# 先算 log_return，用 forward-filled price
reserves["log_return"] = np.log(reserves["price"] / reserves["price"].shift(1))

# RV (NaN 仍在最前 WINDOW-1 列)
WINDOW = 86400 // BLOCK_INTERVAL_SECONDS
reserves["RV"] = (reserves["log_return"]
                  .rolling(window=WINDOW, min_periods=WINDOW)
                  .apply(lambda x: np.sqrt(np.nansum(x**2))))

reserves = reserves.drop(columns=[
    "reserve0", "reserve1", "r0_h", "r1_h", "log_return"
])
block_price_map = reserves.set_index("blockNumber")["price"].to_dict()

# ------------------------------------------------------------
# 3‧ Swap 五分類 → 只留 sell0 / sell1
# ------------------------------------------------------------
sell0 = (swaps_df["amount0In"]  > 0) & (swaps_df["amount1Out"] > 0) & \
        (swaps_df["amount0Out"] == 0) & (swaps_df["amount1In"]  == 0)   # 賣 USD，買 ETH

sell1 = (swaps_df["amount1In"]  > 0) & (swaps_df["amount0Out"] > 0) & \
        (swaps_df["amount1Out"] == 0) & (swaps_df["amount0In"]  == 0)   # 賣 ETH，買 USD

valid_swaps = swaps_df[sell0 | sell1].copy()
other_swaps = swaps_df[~(sell0 | sell1)].copy()

# ─────────────────────────────────────────────────────────────
# 3-1：轉人類單位
# ─────────────────────────────────────────────────────────────
valid_swaps["amount0In_h"]  = valid_swaps["amount0In"]  / 10**DEC0
valid_swaps["amount1In_h"]  = valid_swaps["amount1In"]  / 10**DEC1
valid_swaps["amount0Out_h"] = valid_swaps["amount0Out"] / 10**DEC0
valid_swaps["amount1Out_h"] = valid_swaps["amount1Out"] / 10**DEC1

valid_swaps["netIn0_h"] = valid_swaps["amount0In_h"] * (1 - FEE_RATE)
valid_swaps["netIn1_h"] = valid_swaps["amount1In_h"] * (1 - FEE_RATE)

# ------------------------------------------------------------
# 4‧ 每筆 swap 的價格、USD 成交量、手續費
# ------------------------------------------------------------
mask_sell0 = sell0.loc[valid_swaps.index]
mask_sell1 = sell1.loc[valid_swaps.index]

# 分母 (denominator) – 全部是 ETH 數量
den0 = valid_swaps.loc[mask_sell0, "amount1Out_h"].replace(0, np.nan)    # 收到 ETH
den1 = valid_swaps.loc[mask_sell1, "netIn1_h"].replace(0, np.nan)        # 付出 ETH (淨)

# 價格 (USD / ETH)
price = np.full(len(valid_swaps), np.nan)
price[mask_sell0] = valid_swaps.loc[mask_sell0, "netIn0_h"]     / den0   # 賣 USD
price[mask_sell1] = valid_swaps.loc[mask_sell1, "amount0Out_h"] / den1   # 賣 ETH

# 若價格算不出來 → 補池子 mid-price
nan_idx = np.isnan(price)
if nan_idx.any():
    valid_swaps.loc[nan_idx, "price"] = valid_swaps.loc[nan_idx, "blockNumber"].map(block_price_map)
valid_swaps.loc[~nan_idx, "price"] = price[~nan_idx]

# 成交量 (USD)
valid_swaps["volume"] = np.where(
    mask_sell0,
    valid_swaps["amount0In_h"],                         # 已經是 USD
    valid_swaps["amount1In_h"] * valid_swaps["price"]   # ETH × (USD/ETH)
)

# 手續費 (USD)
valid_swaps["fee"] = valid_swaps["volume"] * FEE_RATE

# ------------------------------------------------------------
# 5‧ flash / dust → volume、fee 歸零
# ------------------------------------------------------------
other_swaps["volume"] = 0
other_swaps["fee"]    = 0

# ============================================================
# 6‧ 區塊聚合
# ============================================================
swaps_blk = (
    pd.concat([valid_swaps, other_swaps], ignore_index=True)
      .groupby("blockNumber", as_index=False)[["volume", "fee"]]
      .sum()
)

# ============================================================
# 7‧ merge & 輸出
# ============================================================
merged = reserves.merge(swaps_blk, on="blockNumber", how="left")
merged[["volume", "fee"]] = merged[["volume", "fee"]].fillna(0)

merged["pool_value"] = merged["pool_value"].apply(int)
merged.to_csv(OUTPUT_CSV, index=False)
print(f"✅ 完成！{OUTPUT_CSV}  (rows = {len(merged):,})")
