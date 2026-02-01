import xarray as xr
import pandas as pd
import os

# 1. 加载站点坐标数据
stations_df = pd.read_csv('station_coordinates.csv')

def nc_to_CSV(nc_path):

    # 2. 打开 .nc 文件
    ds = xr.open_dataset(nc_path)
    all_station_data = []

    for index, row in stations_df.iterrows():
        stn_name = row['Name']
        stn_lat = row['Latitude']
        stn_lon = row['Longitude']

        try:
            subset = ds.sel(lat=stn_lat, lon=stn_lon, method='nearest')

            # 将提取的数据转换为 Pandas DataFrame
            # 如果 .nc 是时间序列数据，这会生成一个时间序列列表
            temp_df = subset.to_dataframe().reset_index()

            # 添加站点元数据，方便区分
            temp_df['Station_Name'] = stn_name
            temp_df['Target_Lat'] = stn_lat
            temp_df['Target_Lon'] = stn_lon

            all_station_data.append(temp_df)

        except Exception as e:
            print(f"站点 {stn_name} 提取失败: {e}")

    # 3. 合并所有数据并保存
    if all_station_data:
        final_output = pd.concat(all_station_data, ignore_index=True)
        folder_name = 'CSV'

        # 2. 如果文件夹不存在，则创建它
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # 3. 构建新的保存路径
        # os.path.basename(nc_path) 会提取文件名（例如 'data.nc'），避免带入旧的路径前缀
        file_name = os.path.basename(nc_path).split('.')[0] + '.csv'
        output_file = os.path.join(folder_name, file_name)

        # 4. 保存为 CSV
        final_output.to_csv(output_file, index=False)
        print("已保存" + output_file)
    else:
        print(" 未提取到任何数据。")


# 增加过滤，只读取 .nc 文件，防止读取到隐藏文件
nc_names = [f for f in os.listdir('Data') if f.endswith('.nc')]
data_folder = 'Data'
output_folder = 'CSV'
total_files = len(nc_names)
bad_files = []
for i, nc in enumerate(nc_names):
    # 1. 构造输入和输出的完整路径
    full_nc_path = os.path.join(data_folder, nc)

    # 构造对应的 CSV 文件名 (去掉 .nc，加上 .csv)
    base_name = os.path.splitext(nc)[0]
    csv_file_path = os.path.join(output_folder, f"{base_name}.csv")

    # 2. 检查文件是否已存在
    if os.path.exists(csv_file_path):
        continue

    # 3. 如果不存在，则执行转换
    try:
        nc_to_CSV(full_nc_path)

    except Exception as e:
        print(f"❌ 文件已损坏，无法打开: {nc}")
        os.remove(full_nc_path)
        print(f"   已成功删除坏文件: {nc}")
        continue  # 跳过这个坏文件，继续处理下一个

print("任务全部执行完毕！")