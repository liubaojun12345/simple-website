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

ETF_SYMBOL = "588000"
ETF_NAME = "科创50ETF"


def get_option_chain_data():
    print(f"正在获取 {ETF_NAME}({ETF_SYMBOL}) 期权实时行情...")
    try:
        # option_finance_board 参数: "科创50ETF期权"
        df_all = ak.option_finance_board("科创50ETF期权")
        print(f"获取到 {len(df_all)} 个合约")
        print(f"列名: {list(df_all.columns)}")

        if len(df_all) == 0:
            print("未获取到数据")
            return None

        all_contracts = df_all.to_dict('records')
        print(f"处理 {len(all_contracts)} 个合约")

        price_data = ak.option_sse_underlying_spot_price_sina()
        current_etf_price = None
        for item in price_data:
            if item.get('code', '') == ETF_SYMBOL:
                current_etf_price = float(item.get('price', 0))
                break

        print(f"{ETF_NAME} 当前价格: {current_etf_price}")

        result = []
        for row in all_contracts:
            try:
                code = str(row['code'])
                strike = float(row['strike_price'])
                cp = '认购' if row['cp'] == 1 else '认沽'

                last_price = float(row['last']) if pd.notna(row.get('last')) else None
                bid_price = float(row['bid']) if pd.notna(row.get('bid')) else None
                ask_price = float(row['ask']) if pd.notna(row.get('ask')) else None
                iv = float(row['implied_volatility']) * 100 if pd.notna(row.get('implied_volatility')) else None

                delta = float(row['delta']) if pd.notna(row.get('delta')) else None
                gamma = float(row['gamma']) if pd.notna(row.get('gamma')) else None
                theta = float(row['theta']) if pd.notna(row.get('theta')) else None
                vega = float(row['vega']) if pd.notna(row.get('vega')) else None

                volume = int(row['volume']) if pd.notna(row.get('volume')) else 0
                open_interest = int(row['open_interest']) if pd.notna(row.get('open_interest')) else 0

                if current_etf_price is not None and iv is not None:
                    if cp == '认购':
                        intrinsic = max(current_etf_price - strike, 0)
                    else:
                        intrinsic = max(strike - current_etf_price, 0)
                    if last_price is not None:
                        time_value = round(last_price - intrinsic, 4)
                    else:
                        time_value = 0
                else:
                    intrinsic = 0
                    time_value = 0

                expire_date = row.get('expire_date', '')
                if expire_date:
                    expire_date = str(int(expire_date))
                    if len(expire_date) == 8:
                        expire_date = f"{expire_date[0:4]}-{expire_date[4:6]}-{expire_date[6:8]}"

                result.append({
                    "code": code,
                    "name": f"科创50{cp[0]}{str(expire_date)[2:6]}",
                    "cp": cp,
                    "strike_price": float(strike),
                    "last_price": last_price,
                    "bid_price": bid_price,
                    "ask_price": ask_price,
                    "volume": volume,
                    "open_interest": open_interest,
                    "implied_volatility": iv,
                    "delta": delta,
                    "gamma": gamma,
                    "theta": theta,
                    "vega": vega,
                    "expiration_date": expire_date,
                    "intrinsic_value": round(intrinsic, 4),
                    "time_value": round(time_value, 4),
                    "underlying_price": round(current_etf_price, 3) if current_etf_price is not None else None
                })
            except Exception as e:
                print(f"跳过异常合约 {code if 'code' in locals() else 'unknown'}: {e}")
                continue

        expiration_dates = sorted(list(set([item['expiration_date'] for item in result if item['expiration_date']])))

        output = {
            "etf_name": ETF_NAME,
            "etf_symbol": ETF_SYMBOL,
            "current_etf_price": round(current_etf_price, 3) if current_etf_price is not None else None,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expiration_dates": expiration_dates,
            "options": result
        }

        print(f"处理完成: {len(result)} 个有效合约")
        return output
    except Exception as e:
        print(f"整体获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    data = get_option_chain_data()
    if not data:
        print("生成失败")
        return

    # 读取现有HTML文件
    with open('option-chain-static.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 找到数据起始行，替换到结束
    new_lines = []
    skip = False
    for line in lines:
        if '// 预加载科创50ETF期权' in line:
            # 开始替换
            skip = True
            new_lines.append(line.rstrip('\n'))
            new_lines.append(f"// 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            new_lines.append("// 由 generate-option-chain-static.py 自动生成")
            new_lines.append(f"const staticOptionData = {json.dumps(data, indent=2)};")
            continue
        if '};' in line and '</script>' in line and skip:
            # 结束替换，不再添加原来的数据
            skip = False
            new_lines.append('</script>')
            continue
        if not skip:
            new_lines.append(line.rstrip('\n'))

    with open('option-chain-static.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print("✅ 已成功更新 option-chain-static.html")
    print("\n下一步:")
    print("  git add option-chain-static.html")
    print("  git commit -m '更新期权行情'")
    print("  git push origin master")
    print("GitHub Pages 会在几分钟后更新")


if __name__ == "__main__":
    main()
