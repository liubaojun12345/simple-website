#!/usr/bin/env python3
import akshare as ak
import pandas as pd

df = ak.option_sse_list_sina()
print("Type:", type(df))
print("Length:", len(df))
if len(df) > 0:
    print("\nFirst item:", df[0])
