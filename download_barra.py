import requests
import os
from tqdm import tqdm
import time


def download_nci_file(url, save_path, max_retries=5):

    for attempt in range(max_retries):
        try:
            # 1. 获取本地已下载的大小
            temp_size = os.path.getsize(save_path) if os.path.exists(save_path) else 0

            # 2. 设置请求头，请求从上次断开的位置开始
            headers = {'Range': f'bytes={temp_size}-'}

            # 使用 stream=True
            response = requests.get(url, headers=headers, stream=True, timeout=30)

            # 状态码 206 表示服务器支持断点续传 (Partial Content)
            # 状态码 200 表示服务器不支持，会重新开始下
            # 状态码 416 表示请求范围不符合（通常是本地文件已经下完了）
            if response.status_code == 416:
                print(f"文件已完整或请求范围错误，跳过: {os.path.basename(save_path)}")
                return True

            response.raise_for_status()

            # 获取剩余部分的大小并加上已下载的大小，得到文件总大小
            total_size = int(response.headers.get('content-length', 0)) + temp_size

            # 3. 以 'ab' (追加) 模式写入
            with open(save_path, 'ab') as f, tqdm(
                    desc=os.path.basename(save_path),
                    total=total_size,
                    initial=temp_size,  # 进度条从本地大小开始
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024 * 1024):
                    if data:
                        f.write(data)
                        bar.update(len(data))

            return True

        except Exception as e:
            print(f"\n网络中断 (尝试 {attempt + 1}/{max_retries}): {e}")

    return False

# 基础 URL
base_url = "https://thredds.nci.org.au/thredds/fileServer/ob53/output/reanalysis/AUS-11/BOM/ERA5/historical/hres/BARRA-R2/v1/1hr/tas/latest/"

file_list = [f"tas_AUS-11_ERA5_historical_hres_BOM_BARRA-R2_v1_1hr_{year}{month:02d}-{year}{month:02d}.nc"
             for year in range(1979,2026)
             for month in range(1, 13)]

save_dir = "Data"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

print(f"开始下载，共 {len(file_list)} 个文件...")
for file_name in file_list:
    full_url = base_url + file_name
    dest_path = os.path.join(save_dir, file_name)
    download_nci_file(full_url, dest_path)

print("全部任务处理完成。")