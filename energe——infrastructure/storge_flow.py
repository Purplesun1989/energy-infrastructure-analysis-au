import csv

# 设置文件名
input_file = 'GasBBActualFlowStorage/GasBBActualFlowStorage.csv'
output_All = 'Filtered_All.csv'
output_Pipe = 'Filtered_Pipeline.csv'
output_Stor = 'Filtered_Storage.csv'

target_states = ['NSW', 'QLD', 'SA', 'VIC']

with open(input_file, mode='r', encoding='utf-8') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames

    # 同时打开三个输出文件
    with open(output_All, 'w', encoding='utf-8', newline='') as f_all, \
            open(output_Pipe, 'w', encoding='utf-8', newline='') as f_pipe, \
            open(output_Stor, 'w', encoding='utf-8', newline='') as f_stor:

        # 为三个文件分别创建写入器
        writer_all = csv.DictWriter(f_all, fieldnames=fieldnames)
        writer_pipe = csv.DictWriter(f_pipe, fieldnames=fieldnames)
        writer_stor = csv.DictWriter(f_stor, fieldnames=fieldnames)

        # 写入三个文件的表头
        writer_all.writeheader()
        writer_pipe.writeheader()
        writer_stor.writeheader()

        # 只遍历一遍原始文件（效率最高！）
        for row in reader:
            state = row['State']
            facility_type = row['FacilityType']

            # 检查州是否符合要求
            if state in target_states:

                # 情况 A：属于 Pipeline 或 Storage (或者是 Compressor)
                # 注意：这里建议包含 'COMP'，因为它是管道的一部分
                if facility_type in ['PIPE', 'STORAGE', 'COMP']:
                    writer_all.writerow(row)

                # 情况 B：专门存入 Pipeline 文件
                if facility_type == 'PIPE' or facility_type == 'COMP':
                    writer_pipe.writerow(row)

                # 情况 C：专门存入 Storage 文件
                # 请检查你的原始数据里是 'STORAGE' 还是 'STOR'
                if facility_type == 'STORAGE' or facility_type == 'STOR':
                    writer_stor.writerow(row)

print("处理完成！三个文件已生成：")
print(f"1. 总表: {output_All}")
print(f"2. 管道表: {output_Pipe}")
print(f"3. 存储表: {output_Stor}")