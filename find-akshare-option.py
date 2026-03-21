#!/usr/bin/env python3
import akshare as ak
import inspect

# 打印所有option相关函数
print("akshare 中 option 相关函数:")
for name, func in inspect.getmembers(ak):
    if 'option' in name.lower():
        print(f"- {name}")
