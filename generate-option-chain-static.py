#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成科创50ETF(588000)期权静态HTML页面
用于GitHub Pages，不需要后端服务，直接访问即可
用法: python generate-option-chain-static.py -> 自动生成 option-chain-static.html
"""

import akshare as ak
import pandas as pd
import json
from datetime import datetime

ETF_SYMBOL = "588000"  # 科创50ETF
ETF_NAME = "科创50ETF"

def get_option_chain_data():
    """获取期权数据 - 适配最新 akshare 接口，使用新浪数据源"""
    print(f"正在获取 {ETF_NAME}({ETF_SYMBOL}) 期权实时行情...")
    
    try:
        # 获取上交所期权所有年份
        years = ak.option_sse_list_sina()
        print(f"获取到年份列表: {years}")
        
        all_contracts = []
        # 对每个年份获取合约列表
        for year in years:
            try:
                df_year = ak.option_sse_daily_sina(str(year))
                print(f"年份 {year}: {len(df_year)} 个合约")
                all_contracts.extend(df_year.to_dict('records'))
            except Exception as e:
                print(f"获取年份 {year} 失败: {e}")
                continue
        
        print(f"总共 {len(all_contracts)} 个合约")
        
        # 筛选对应ETF的期权
        # 科创50ETF期权: 认购 10588xxxx, 认沽 10589xxxx
        filtered_contracts = []
        for contract in all_contracts:
            code = str(contract.get('code', ''))
            if code.startswith('10588') or code.startswith('10589'):
                filtered_contracts.append(contract)
        
        print(f"筛选后 {len(filtered_contracts)} 个 {ETF_NAME} 期权合约")
        
        # 获取当前ETF价格
        price_data = ak.option_sse_underlying_spot_price_sina()
        # price_data is list of dicts
        current_etf_price = None
        for item in price_data:
            if item.get('code', '') == ETF_SYMBOL:
                current_etf_price = float(item.get('price', 0))
                break
        
        print(f"{ETF_NAME} 当前价格: {current_etf_price}")
        
        # 获取期权行情和希腊值
        result = []
        for row in filtered_contracts:
            try:
                code = str(row['code'])
                # 获取单个期权详细行情和希腊值
                detail = ak.option_sse_greeks_sina(code)
                if len(detail) == 0:
                    continue
                
                d = detail.iloc[0]
                
                strike = float(row['strike_price'])
                cp = row['call_put']  # 认购/认沽
                last_price = float(d['last']) if pd.notna(d['last']) else None
                bid_price = float(d['bid']) if pd.notna(d['bid']) else None
                ask_price = float(d['ask']) if pd.notna(d['ask']) else None
                iv = float(d['implied_volatility']) * 100 if pd.notna(d['implied_volatility']) else None
                
                if current_etf_price and iv is not None:
                    if cp == '认购':
                        intrinsic = max(current_etf_price - strike, 0)
                    else:
                        intrinsic = max(strike - current_etf_price, 0)
                    if last_price:
                        time_value = round(last_price - intrinsic, 4)
                    else:
                        time_value = 0
                else:
                    intrinsic = 0
                    time_value = 0
                
                # 格式化到期日
                expire_date = row.get('expire_date', '')
                if expire_date and len(expire_date) == 8:
                    # 格式化为 YYYY-MM-DD
                    expire_date = f"{expire_date[0:4]}-{expire_date[4:6]}-{expire_date[6:8]}"
                
                result.append({
                    "code": code,
                    "name": row.get('name', code),
                    "cp": cp,
                    "strike_price": float(strike),
                    "last_price": last_price,
                    "bid_price": bid_price,
                    "ask_price": ask_price,
                    "volume": int(d['volume']) if pd.notna(d['volume']) else 0,
                    "open_interest": int(d['open_interest']) if pd.notna(d['open_interest']) else 0,
                    "implied_volatility": iv,
                    "delta": float(d['delta']) if pd.notna(d['delta']) else None,
                    "gamma": float(d['gamma']) if pd.notna(d['gamma']) else None,
                    "theta": float(d['theta']) if pd.notna(d['theta']) else None,
                    "vega": float(d['vega']) if pd.notna(d['vega']) else None,
                    "expiration_date": expire_date,
                    "intrinsic_value": round(intrinsic, 4),
                    "time_value": round(time_value, 4),
                    "underlying_price": round(current_etf_price, 3) if current_etf_price else None
                })
            except Exception as e:
                print(f"跳过异常合约 {code if 'code' in locals() else 'unknown'}: {e}")
                continue
        
        expiration_dates = sorted(list(set([item['expiration_date'] for item in result])))
        
        output = {
            "etf_name": ETF_NAME,
            "etf_symbol": ETF_SYMBOL,
            "current_etf_price": round(current_etf_price, 3) if current_etf_price else None,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expiration_dates": expiration_dates,
            "options": result
        }
        
        print(f"处理完成: {len(result)} 个有效合约")
        return output
        
        result = []
        for _, row in df.iterrows():
            try:
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
                    "cp": row['cp'],
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
                print(f"跳过异常合约: {e}")
                continue
        
        expiration_dates = sorted(list(set([item['expiration_date'] for item in result])))
        
        output = {
            "etf_name": ETF_NAME,
            "etf_symbol": ETF_SYMBOL,
            "current_etf_price": round(float(df['underlying_price'].iloc[0]), 3) if len(df) > 0 else None,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expiration_dates": expiration_dates,
            "options": result
        }
        
        print(f"处理完成: {len(result)} 个有效合约")
        return output
    
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None

def generate_static_html(data):
    """读取模板，插入数据，生成静态HTML"""
    
    with open('option-chain.html', 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 在HTML末尾插入全局数据
    script_inject = f"""
<script>
// 预加载静态数据（由 generate-option-chain-static.py 生成）
const staticOptionData = {json.dumps(data, indent=2)};
</script>
"""
    
    # 修改初始化逻辑，优先使用静态数据
    modify_js = """
        // 如果有预加载的静态数据，直接使用
        if (typeof staticOptionData !== 'undefined') {
            console.log('使用预生成的静态数据');
            allData = staticOptionData;
            updateInfo();
            populateFilters();
            renderTable();
            document.getElementById('loading').style.display = 'none';
            document.getElementById('optionTable').style.display = 'table';
        }
"""
    
    # 在window.onload末尾添加
    template = template.replace(
        "        // 页面加载完成\n        window.onload = function() {\n            loadData();\n            setupAutoRefresh();\n        };",
        "        // 页面加载完成\n        window.onload = function() {\n            " + modify_js + "\n            loadData();\n            setupAutoRefresh();\n        };"
    )
    
    # 插入静态数据
    template = template.replace("</body>\n</html>", script_inject + "\n</body>\n</html>")
    
    with open('option-chain-static.html', 'w', encoding='utf-8') as f:
        f.write(template)
    
    print("已生成静态页面: option-chain-static.html")

def main():
    data = get_option_chain_data()
    if data:
        generate_static_html(data)
        print("\n使用方法:")
        print("1. 将 option-chain-static.html 上传到 GitHub")
        print("2. 访问 GitHub Pages 就能看到最新行情了")
        print("3. 需要更新数据时，重新运行这个脚本再提交即可")
    else:
        print("生成失败")

if __name__ == "__main__":
    main()
