import pandas as pd
import numpy as np

# 1. 載入事件資料
swaps_df = pd.read_csv('USDC_WBNB_swaps.csv')
syncs_df = pd.read_csv('USDC_WBNB_syncs.csv')

# 2. 計算每個區塊的保留量（取每區塊最後一次 Sync）
reserves = syncs_df.sort_values('blockNumber') \
                   .groupby('blockNumber', as_index=False) \
                   .last()

# 3. 計算價格 (token0 in token1 單位)
reserves['price'] = reserves['reserve1'] / reserves['reserve0']

# 4. 聚合每個區塊的 Swap 交易量
swaps_df['volume0'] = swaps_df['amount0In'] + swaps_df['amount0Out']
swaps_df['volume1'] = swaps_df['amount1In'] + swaps_df['amount1Out']

volume = swaps_df.groupby('blockNumber', as_index=False) \
                 .agg({'volume0':'sum', 'volume1':'sum'})

# 5. 合併 Reserves 與 Volume
df = pd.merge(reserves, volume, on='blockNumber', how='left').fillna(0)

# 6. 計算交易量價值 (以 token1 單位)
df['volume_value_token1'] = df['volume0'] * df['price'] + df['volume1']

# 7. 計算價格波動率 (log return 的標準差)
df['log_return'] = np.log(df['price'] / df['price'].shift(1))
volatility = df['log_return'].std()

# 8. 顯示結果
print(f"價格波動率 (log-return std): {volatility:.6f}")
