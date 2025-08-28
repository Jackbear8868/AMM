import pandas as pd
import numpy as np
pd.set_option("display.float_format", "{:.6f}".format)

# ============================================================
# 0‧ 基本參數（修改這裡就好）
# ============================================================
SWAP_FILE  = "USDT_WBNB_swaps.csv"
SYNC_FILE  = "USDT_WBNB_syncs.csv"
OUTPUT_CSV = "USDT_WBNB_token1.csv"

DEC0 = 18      # ★ token0 decimals（例：WETH/WBNB = 18）
DEC1 = 6       # ★ token1 decimals（例：USDT/USDC = 6）

FEE_RATE   = 0.003
BLOCK_INTERVAL_SECONDS = 12

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

# ------------------------------------------------------------------
# 2. reserves：先補「完整區塊序列」，再 forward-fill
# ------------------------------------------------------------------
raw = (syncs_df.sort_values("blockNumber")
                 .groupby("blockNumber", as_index=False)
                 .last())

first_blk = int(raw["blockNumber"].min())
last_blk  = int(raw["blockNumber"].max())
all_blocks = pd.DataFrame({"blockNumber":
                           np.arange(first_blk, last_blk + 1, dtype="int64")})

reserves = (all_blocks.merge(raw, on="blockNumber", how="left")
                     .ffill())                       # 補洞

# 2-1 人類單位
reserves["r0_h"] = reserves["reserve0"] / 10**DEC0       # WBNB
reserves["r1_h"] = reserves["reserve1"] / 10**DEC1       # USDT

# 2-2 Mid — 注意方向：USDT / WBNB
reserves["price"] = reserves["r1_h"] / reserves["r0_h"]
reserves["price"] = reserves["price"].astype(np.float64)

# 2-3 pool_value 與 RV
reserves["log_return"] = np.log(reserves["price"] / reserves["price"].shift(1))
reserves["pool_value"] = reserves["r0_h"] * reserves["price"] + reserves["r1_h"]

WINDOW = 86400 // BLOCK_INTERVAL_SECONDS
reserves["RV"] = (reserves["log_return"]
                  .rolling(window=WINDOW, min_periods=WINDOW)
                  .apply(lambda x: np.sqrt(np.nansum(x**2))))

reserves = reserves.drop(columns=[
    "reserve0", "reserve1", "r0_h", "r1_h", "log_return"])
block_price_map = reserves.set_index("blockNumber")["price"].to_dict()

# ------------------------------------------------------------
# 3‧ Swap 五分類 → 只留 sell0 / sell1
# ------------------------------------------------------------
sell0 = (swaps_df["amount0In"]  > 0) & (swaps_df["amount1Out"] > 0) & \
        (swaps_df["amount0Out"] == 0) & (swaps_df["amount1In"]  == 0)

sell1 = (swaps_df["amount1In"]  > 0) & (swaps_df["amount0Out"] > 0) & \
        (swaps_df["amount1Out"] == 0) & (swaps_df["amount0In"]  == 0)

valid_swaps = swaps_df[sell0 | sell1].copy()
other_swaps = swaps_df[~(sell0 | sell1)].copy()

# ─────────────────────────────────────────────────────────────
# 3-1 轉人類單位
# ─────────────────────────────────────────────────────────────
valid_swaps["amount0In_h"]  = valid_swaps["amount0In"]  / (10**DEC0)
valid_swaps["amount1In_h"]  = valid_swaps["amount1In"]  / (10**DEC1)
valid_swaps["amount0Out_h"] = valid_swaps["amount0Out"] / (10**DEC0)
valid_swaps["amount1Out_h"] = valid_swaps["amount1Out"] / (10**DEC1)

# ★★ (A) 手續費後淨額──保證欄位存在 ★★
valid_swaps["netIn0_h"] = valid_swaps["amount0In_h"] * (1 - FEE_RATE)
valid_swaps["netIn1_h"] = valid_swaps["amount1In_h"] * (1 - FEE_RATE)

# ------------------------------------------------------------
# 4‧ 計算每筆 swap 的成交「價格、USD 成交量、USD 手續費」
# ------------------------------------------------------------
mask_sell0 = (valid_swaps["amount0In"]  > 0)   & (valid_swaps["amount1Out"] > 0) & \
             (valid_swaps["amount0Out"] == 0) & (valid_swaps["amount1In"]  == 0)

mask_sell1 = (valid_swaps["amount1In"]  > 0)   & (valid_swaps["amount0Out"] > 0) & \
             (valid_swaps["amount1Out"] == 0) & (valid_swaps["amount0In"]  == 0)

# ── 賣 token0 → 分母 = ETH 淨額
den0 = valid_swaps.loc[mask_sell0, "netIn0_h"].replace(0, np.nan)
# ── 賣 token1 → 分母 = ETH 收到量
den1 = valid_swaps.loc[mask_sell1, "amount0Out_h"].replace(0, np.nan)

price = np.full(len(valid_swaps), np.nan)
price[mask_sell0]  = valid_swaps.loc[mask_sell0, "amount1Out_h"] / den0  # USD / ETH
price[mask_sell1]  = valid_swaps.loc[mask_sell1, "netIn1_h"]     / den1  # USD / ETH

# NaN → 用池子 mid-price 補
nan_idx = np.isnan(price)
if nan_idx.any():
    valid_swaps.loc[nan_idx, "price"] = valid_swaps.loc[nan_idx, "blockNumber"].map(block_price_map)
valid_swaps.loc[~nan_idx, "price"] = price[~nan_idx]

# 4-2 成交量以「USD 面值」計算 ------------------------------  ###  <-- 變動
valid_swaps["volume"] = np.where(
    mask_sell0,
    valid_swaps["amount0In_h"] * valid_swaps["price"],   # ETH × (USDT/ETH)
    valid_swaps["amount1In_h"]                           # 已經是 USDT
)

# 4-3 手續費同樣取 USD 面值 -------------------------------  ###  <-- 變動
valid_swaps["fee"] = valid_swaps["volume"] * FEE_RATE

# ------------------------------------------------------------
# 5‧ flash / dust → volume、fee 都設 0（USDT）
# ------------------------------------------------------------
other_swaps["volume"] = 0
other_swaps["fee"]    = 0

# ============================================================
# 6‧ 區塊聚合
# ============================================================
swaps_blk = (
    pd.concat([valid_swaps, other_swaps], ignore_index=True)
      .groupby("blockNumber", as_index=False)[["volume", "fee",]]
      .sum()
)

# swaps_blk = (
#     pd.concat([valid_swaps, other_swaps], ignore_index=True)
#       .groupby("blockNumber", as_index=False)[["volume", "fee", "amount0In_h", "amount1In_h", "amount0Out_h", "amount1Out_h"]]
#       .sum()
# )



# ============================================================
# 7‧ merge & 輸出
# ============================================================
merged = reserves.merge(swaps_blk, on="blockNumber", how="left")
merged[["volume", "fee"]] = merged[["volume", "fee"]].fillna(0)

merged['pool_value'] = merged['pool_value'].apply(int)
merged.to_csv(OUTPUT_CSV, index=False)
print(f"✅ 完成！{OUTPUT_CSV}  (rows = {len(merged):,})")
