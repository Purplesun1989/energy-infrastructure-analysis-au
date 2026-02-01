import json
import requests
import pandas as pd
import time
import os

# 1. 基础配置
JSON_FILE = 'stationlist.json'
# 注意：BASE_URL 必须是这个物理路径，否则会 404
BASE_URL = "https://www.bom.gov.au/climate/data/acorn-sat/stations/data/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bom.gov.au/climate/data/acorn-sat/'
}
TARGET_STATES = ['NSW', 'QLD', 'SA', 'VIC.','VIC']


def main():
    # 读取保存的 ID 列表
    if not os.path.exists(JSON_FILE):
        print(f"错误: 找不到 {JSON_FILE} 文件")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        stations = json.load(f)

    all_data = []  # 这是你的“蓄水池”，用来存放所有过滤后的站点字典
    print(f"开始处理，总计 {len(stations)} 个站点...")

    for stn in stations:
        stn_id = stn.get('id')
        if not stn_id or stn_id == "0":
            continue


        try:
            # 请求详情数据
            response = requests.get(f"{BASE_URL}{stn_id}.details.json", headers=HEADERS, timeout=10)

            if response.status_code == 200:
                raw_json = response.json()
                # 定位到数据核心层
                station_info = raw_json['acorn_sat_catalogue']['station']

                # 提取并清洗州名
                state_val = station_info['locality'].split(',')[-1].strip().upper()

                if state_val in TARGET_STATES:
                    flat_data = {
                        'Site_Number': station_info['stn_num'],
                        'Name': station_info['site_name'],
                        'State': state_val,
                        'Latitude': float(station_info['latitude']),
                        'Longitude': float(station_info['longitude']),
                        'Elevation': float(station_info['elevation']),
                        'Start_Year': station_info['data_begin_year']
                    }

                    if flat_data['State'] == 'VIC.':
                        flat_data['State'] = 'VIC'

                    all_data.append(flat_data)
                    # print(f"  已加入列表 (州: {state_val})")
                else:
                    print(f"  跳过 (非目标州: {state_val})")

            # 礼貌爬取
            time.sleep(0.5)

        except Exception as e:
            print(f" 站点 {stn_id} 抓取失败: {e}")

    if all_data:
        # 将“列表套字典”直接转为 Pandas DataFrame
        df = pd.DataFrame(all_data)
        csv_name = 'station_coordinates.csv'
        df.to_csv(csv_name, index=False, encoding='utf-8-sig')

        print(f" CSV 已保存至: {csv_name}")
    else:
        print("未能成功获取任何符合目标州条件的数据。")


if __name__ == "__main__":
    main()