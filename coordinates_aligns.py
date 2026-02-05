import geopandas as gpd
import pandas as pd
import os
import gc
import time

def read_gdf():

    # 1. 读取数据
    counties = gpd.read_file("Data/tl_2025_us_county/tl_2025_us_county.shp", engine="pyogrio")

    # 读取 HUC12 (FileGDB)
    hucs = gpd.read_file("Data/WBD_National_GDB/WBD_National_GDB.gdb", layer="WBDHU12", engine="pyogrio")

    # 2. 统一并投影坐标系 (核心步骤)
    # 定义目标坐标系：Albers 等面积投影
    target_crs = "EPSG:5070"
    # 转换县边界
    counties = counties.to_crs(target_crs)
    # 转换 HUC12 (这个步骤对 8万多个多边形来说比较耗时，请耐心等待)
    hucs = hucs.to_crs(target_crs)
    # 3. 验证坐标系
    print(f"县边界当前 CRS: {counties.crs}")
    print(f"HUC12 当前 CRS: {hucs.crs}")

    if counties.crs == hucs.crs:
        print("坐标系已成功统一！")

    # 将投影后的结果保存到新文件
    counties.to_file("Data/processed_counties_5070.gpkg", driver="GPKG")
    hucs.to_file("Data/processed_hucs_12_5070.gpkg", driver="GPKG")



def get_intersections():

    # 1. 使用 pyogrio 引擎极速读取
    print("正在读取预处理数据...")
    # 尽量只读取需要的列，节省内存
    counties = gpd.read_file("Data/processed_counties_5070.gpkg", engine="pyogrio")
    hucs = gpd.read_file("Data/processed_hucs_12_5070.gpkg", engine="pyogrio")
    # 2. 预计算总面积
    counties['county_area_total'] = counties.geometry.area
    hucs['huc12_area_total'] = hucs.geometry.area

    # 3. 提取州代码（GEOID 前两位）用于循环
    # 这样可以分块处理，防止内存崩溃，并提供进度进度条
    counties['state_fips'] = counties['GEOID'].str[:2]
    states = sorted(counties['state_fips'].unique())

    all_results = []

    print(f"开始分州处理，共 {len(states)} 个州/领地...")

    for state in states:
        print(f"正在处理州 FIPS: {state} ... ", end="", flush=True)

        # 筛选当前州的县
        c_sub = counties[counties['state_fips'] == state][['GEOID', 'county_area_total', 'geometry']]

        # 空间索引筛选
        # 只选取与当前州相交的 HUC12，避免处理全美 8 万个多边形
        possible_hucs_idx = hucs.sindex.query(c_sub.unary_union, predicate="intersects")
        h_sub = hucs.iloc[possible_hucs_idx][['huc12', 'huc12_area_total', 'geometry']]

        if h_sub.empty:
            print("跳过（无相交流域）")
            continue

        # 仅对子集进行 overlay
        try:
            res = gpd.overlay(c_sub, h_sub, how='intersection', keep_geom_type=True)

            if not res.empty:
                # 计算碎片面积并计算权重
                res['intersect_area'] = res.geometry.area
                res['w_huc_in_county'] = res['intersect_area'] / res['county_area_total']
                res['w_county_in_huc'] = res['intersect_area'] / res['huc12_area_total']

                # 丢弃几何信息，只存结果数据
                all_results.append(res.drop(columns='geometry'))
                print(f"完成 (新增 {len(res)} 条碎片)")
            else:
                print("无重叠")
        except Exception as e:
            print(f"失败: {e}")

        print(f"州 {state} 处理完成，正在清理内存...")

        # 1. 手动删除不再需要的临时变量
        if 'res' in locals(): del res
        if 'c_sub' in locals(): del c_sub
        if 'h_sub' in locals(): del h_sub

        # 2. 强制启动垃圾回收
        gc.collect()

        # 3. 让 CPU 喘口气
        time.sleep(1)

    # 4. 合并所有州的结果
    final_df = pd.concat(all_results, ignore_index=True)

    # 5. 最终保存
    output_file = "CSV/county_huc12_mapping_weights_optimized.csv"
    final_df.to_csv(output_file, index=False)

    df = pd.read_csv("CSV/county_huc12_mapping_weights_optimized.csv")

def weight_check():

    df = pd.read_csv("CSV/county_huc12_mapping_weights_optimized.csv")
    county_check = df.groupby('GEOID')['w_huc_in_county'].sum()
    print(f"county_check_mean: {county_check.mean():.4f} /1 ")
    huc_check = df.groupby('huc12')['w_county_in_huc'].sum()
    print(f"huc_check.mean: {huc_check.mean():.4f} /1")







if __name__ == "__main__":
    # read_gdf()
    # get_intersections()
    weight_check()

