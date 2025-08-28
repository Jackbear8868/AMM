import pandas as pd

df = pd.read_csv("USDC_ETH.csv")
# df = pd.read_csv("merge.csv")
# df["volume_USDT"] = df["volume"] * df["price"]
# df["fee_USDT"]    = df["fee"]    * df["price"]
# df =df["reserve0", "r0_h","reserve", "r1_h"]
# df.drop(columns=['reserve0', 'reserve1'], inplace=True)
print("\n=== 原始 swaps 中這些 block 的交易 ===")
print(df.head(30))
