#!/usr/bin/env python3
import akshare as ak
import pandas as pd

df = ak.option_sse_list_sina()
print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nFirst 5 rows:")
print(df.head().to_string())

print("\n\n--- Checking ETF price ---")
df_price = ak.option_sse_underlying_spot_price_sina()
print("Shape:", df_price.shape)
print("\nColumns:", df_price.columns.tolist())
print("\nAll:")
print(df_price.to_string())
