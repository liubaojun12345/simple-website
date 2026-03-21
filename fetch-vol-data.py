#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取A股期权波动率数据，生成波动率曲面数据文件
用于 volatility-surface.html 3D可视化
依赖: pip install akshare pandas
"""

import akshare as ak
import pandas as pd
import json

def get_option_chain(symbol: str = "510050"):
    """
    获取50ETF期权链
    symbol: 510050=50ETF, 159915=创业板ETF, 510300=沪深300ETF, 588000=科创50ETF
    """
    print(f"正在获取 {symbol} 期权链...")
    try:
        option_chain = ak.option_sse(symbol=symbol)
        print(f"获取到 {len(option_chain)} 个期权合约")
        return option_chain
    except Exception as e:
        print(f"获取期权链出错: {e}")
        return None

def process_volatility_surface(df):
    """
    处理期权数据，生成波动率曲面
    输出格式: {strikes, expirations, data: [{x, y, z}]}
    x = 行权价
    y = 剩余到期天数
    z = 隐含波动率
    """
    # 筛选出有隐含波动率的数据
    df = df.dropna(subset=['implied_volatility'])
    
    # 整理数据
    strikes = sorted(df['strike_price'].unique().tolist())
    exp_dates = sorted(df['expiration_date'].unique().tolist())
    
    # 计算每个到期日剩余天数
    from datetime import datetime
    today = datetime.today()
    expirations = []
    for exp_date in exp_dates:
        if isinstance(exp_date, str):
            exp_date = datetime.strptime(exp_date, '%Y-%m-%d')
        days = (exp_date - today).days
        if days > 0:
            expirations.append(days)
    
    data = []
    for _, row in df.iterrows():
        strike = float(row['strike_price'])
        exp_date = row['expiration_date']
        if isinstance(exp_date, str):
            exp_date = datetime.strptime(exp_date, '%Y-%m-%d')
        days = (exp_date - today).days
        iv = float(row['implied_volatility'])
        if days > 0 and not pd.isna(iv):
            data.append({
                "x": strike,
                "y": days, 
                "z": iv * 10  # 缩放Z轴让图形更明显
            })
    
    # 去重，每个(strike, days)保留一个IV值
    seen = {}
    unique_data = []
    for point in data:
        key = (round(point['x'], 3), point['y'])
        if key not in seen:
            seen[key] = point
            unique_data.append(point)
    
    result = {
        "strikes": sorted(list(set([round(p['x'], 3) for p in unique_data]))),
        "expirations": sorted(list(set([p['y'] for p in unique_data]))),
        "data": unique_data,
        "width": len(set([round(p['x'], 3) for p in unique_data])),
        "height": len(set([p['y'] for p in unique_data]))
    }
    
    print(f"处理完成: {result['width']} 个行权价, {result['height']} 个到期日, 共 {len(unique_data)} 个数据点")
    return result

def save_to_js(vol_data, filename="real-iv-data.js", etf_name="50ETF"):
    """保存为JS文件，可直接引入HTML"""
    js_content = f"""// {etf_name} 期权隐含波动率曲面数据
// 生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
const volSurfaceData = {json.dumps(vol_data, indent=2)};
"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"数据已保存到 {filename}")

def main():
    # 可以选择不同的ETF
    # 50ETF: 510050
    # 沪深300ETF: 510300
    # 科创50ETF: 588000
    # 创业板ETF: 159915
    
    symbol = "510050"
    etf_name = "50ETF"
    
    df = get_option_chain(symbol)
    if df is None or len(df) == 0:
        print("未获取到数据")
        return
    
    vol_data = process_volatility_surface(df)
    save_to_js(vol_data, "real-iv-data.js", etf_name)
    
    print("\n使用方法:")
    print("1. 将 real-iv-data.js 上传到你的GitHub网站目录")
    print("2. 在 volatility-surface.html 中添加 <script src=\"real-iv-data.js\"></script>")
    print("3. 页面加载后会自动显示真实波动率曲面")

if __name__ == "__main__":
    main()
