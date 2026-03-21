#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科创50ETF(588000) 期权实时行情获取
使用akshare免费接口，自动刷新数据，生成网页可用的json数据供前端显示
依赖: pip install akshare pandas flask
运行: python option-chain-realtime.py
访问: http://localhost:5000/option-chain.html
"""

import akshare as ak
import pandas as pd
import json
import time
from datetime import datetime
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

ETF_SYMBOL = "588000"  # 科创50ETF
ETF_NAME = "科创50ETF"

last_update_time = None
cached_data = None

def get_option_chain_realtime():
    """获取实时期权链行情
    返回处理好的数据
    """
    print(f"[{datetime.now()}] 正在获取 {ETF_NAME}({ETF_SYMBOL}) 期权实时行情...")
    
    try:
        # 获取期权链
        df = ak.option_sse(symbol=ETF_SYMBOL)
        print(f"获取到 {len(df)} 个期权合约")
        
        # 筛选有效数据
        df = df.dropna(subset=['implied_volatility', 'last_price'])
        
        # 处理数据，保留需要的字段
        result = []
        for _, row in df.iterrows():
            try:
                # 计算时间价值 = 期权价格 - (内在价值)
                # 内在价值: 认购 = max(ETF现价 - 行权价, 0)，认沽 = max(行权价 - ETF现价, 0)
                etf_price = float(row['underlying_price']) if pd.notna(row['underlying_price']) else 0
                strike = float(row['strike_price'])
                last_price = float(row['last_price']) if pd.notna(row['last_price']) else 0
                
                if row['cp'] == '认购':
                    intrinsic = max(etf_price - strike, 0)
                else:
                    intrinsic = max(strike - etf_price, 0)
                time_value = round(last_price - intrinsic, 4)
                
                result.append({
                    "code": row['code'],
                    "name": row['name'],
                    "cp": row['cp'],  # 认购/认沽
                    "strike_price": float(strike),
                    "last_price": float(last_price) if pd.notna(row['last_price']) else None,
                    "bid_price": float(row['bid_price']) if pd.notna(row['bid_price']) else None,
                    "ask_price": float(row['ask_price']) if pd.notna(row['ask_price']) else None,
                    "volume": int(row['volume']) if pd.notna(row['volume']) else 0,
                    "open_interest": int(row['open_interest']) if pd.notna(row['open_interest']) else 0,
                    "implied_volatility": round(float(row['implied_volatility']) * 100, 2) if pd.notna(row['implied_volatility']) else None,
                    "delta": float(row['delta']) if pd.notna(row['delta']) else None,
                    "gamma": float(row['gamma']) if pd.notna(row['gamma']) else None,
                    "theta": float(row['theta']) if pd.notna(row['theta']) else None,
                    "vega": float(row['vega']) if pd.notna(row['vega']) else None,
                    "expiration_date": row['expiration_date'],
                    "intrinsic_value": round(intrinsic, 4),
                    "time_value": round(time_value, 4),
                    "underlying_price": round(float(etf_price), 3)
                })
            except Exception as e:
                print(f"处理单条数据出错: {e}")
                continue
        
        # 按到期日分组
        expiration_dates = sorted(list(set([item['expiration_date'] for item in result])))
        
        global last_update_time, cached_data
        last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cached_data = {
            "etf_name": ETF_NAME,
            "etf_symbol": ETF_SYMBOL,
            "current_etf_price": round(float(df['underlying_price'].iloc[0], 3) if len(df) > 0 else None,
            "update_time": last_update_time,
            "expiration_dates": expiration_dates,
            "options": result
        }
        
        print(f"处理完成: {len(result)} 个有效合约，更新时间: {last_update_time}")
        return cached_data
    
    except Exception as e:
        print(f"获取数据出错: {e}")
        return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/option-chain.html')
def option_chain_page():
    return send_from_directory('.', 'option-chain.html')

@app.route('/volatility-surface.html')
def volatility_surface():
    return send_from_directory('.', 'volatility-surface.html')

@app.route('/api/option-chain')
def get_option_chain():
    data = get_option_chain_realtime()
    if data:
        return jsonify({
            "code": 0,
            "message": "success",
            "data": data
        })
    else:
        return jsonify({
            "code": 1,
            "message": "获取数据失败",
            "data": None
        })

@app.route('/api/latest-data')
def get_latest_data():
    global cached_data
    if cached_data:
        return jsonify({
            "code": 0,
            "message": "success",
            "data": {
            "update_time": last_update_time,
            **cached_data
        }
        })
    else:
        return jsonify({
            "code": 1,
            "message": "暂无数据",
            "data": None
        })

if __name__ == "__main__":
    # 启动时先获取一次数据
    get_option_chain_realtime()
    print(f"\n服务已启动，访问: http://127.0.0.1:5000/option-chain.html")
    print("网页会自动每3分钟刷新一次数据\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
