from flask import Flask, request, jsonify
import os
import math
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor
# 移除或注释掉 multiprocessing 相关导入
# import multiprocessing
# Pool = multiprocessing.Pool
# import multiprocessing.shared_memory as shared_memory
from coordTransform_utils import wgs84_to_gcj02
import time

app = Flask(__name__)

# 北京边界坐标（GCJ02）
BEIJING_BOUNDS = {
    'min_lng': 115.70,
    'max_lng': 117.50, 
    'min_lat': 39.40,
    'max_lat': 41.60
}

def is_in_beijing(lng, lat):
    """检查坐标是否在北京范围内"""
    return (BEIJING_BOUNDS['min_lng'] <= lng <= BEIJING_BOUNDS['max_lng'] and
            BEIJING_BOUNDS['min_lat'] <= lat <= BEIJING_BOUNDS['max_lat'])

# 删除 create_shared_heatmap 函数
# def create_shared_heatmap(grid_size=0.01):
#     """创建共享内存的热力图网格（修正维度问题）"""
#     # 计算网格数量
#     lng_size = int((BEIJING_BOUNDS['max_lng'] - BEIJING_BOUNDS['min_lng']) / grid_size) + 1
#     lat_size = int((BEIJING_BOUNDS['max_lat'] - BEIJING_BOUNDS['min_lat']) / grid_size) + 1
#     
#     # 创建共享内存
#     shm = shared_memory.SharedMemory(
#         create=True,
#         size=24*lng_size*lat_size*4  # 24小时×经度×纬度×4字节
#     )
#     # 正确的三维数组reshape
#     heatmap = np.ndarray((24, lng_size, lat_size), dtype=np.int32, buffer=shm.buf)
#     heatmap.fill(0)
#     return shm, (lng_size, lat_size)  # 返回网格尺寸信息

@app.route('/api/heatmap', methods=['POST'])
def get_optimized_heatmap():
    start_time = time.time()
    try:
        data = request.get_json()
        grid_size = float(data.get('grid_width', 0.01))
        target_hour = int(data['hour']) if 'hour' in data else None
        folder_path = data.get('folder_path', 'taxi_log_2008_by_id')

        # 计算网格数量
        lng_size = int((BEIJING_BOUNDS['max_lng'] - BEIJING_BOUNDS['min_lng']) / grid_size) + 1
        lat_size = int((BEIJING_BOUNDS['max_lat'] - BEIJING_BOUNDS['min_lat']) / grid_size) + 1

        # 直接使用主线程内存创建热力图
        heatmap = np.zeros((24, lng_size, lat_size), dtype=np.int32)

        files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
        def process_file(filename):
            nonlocal heatmap
            # print(f"Processing file: {filename}")
            try:
                with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
                    for line in file:
                        parts = line.split(',', 3)
                        if len(parts) < 4:
                            continue
                        try:
                            _, time_str, lng_str, lat_str = parts
                            lng, lat = wgs84_to_gcj02(float(lng_str), float(lat_str))
                            if not is_in_beijing(lng, lat):
                                continue
                            hour = int(time_str[11:13])
                            grid_x = int((lng - BEIJING_BOUNDS['min_lng']) / grid_size)
                            grid_y = int((lat - BEIJING_BOUNDS['min_lat']) / grid_size)
                            if 0 <= grid_x < lng_size and 0 <= grid_y < lat_size:
                                heatmap[hour, grid_x, grid_y] += 1
                        except (ValueError, IndexError):
                            print(f"Error processing line: {line}")
                            continue
            except Exception as e:
                print(f"Error processing file {filename}: {e}")

        with ThreadPoolExecutor(max_workers=200) as executor:
            executor.map(process_file, files)

        result = []
        lng_step = grid_size
        lat_step = grid_size

        if target_hour is not None:
            hour_data = heatmap[target_hour]
            for x in range(lng_size):
                for y in range(lat_size):
                    count = int(hour_data[x, y])
                    if count > 0:
                        result.append({
                            "lng": round(BEIJING_BOUNDS['min_lng'] + x * lng_step + lng_step/2, 6),
                            "lat": round(BEIJING_BOUNDS['min_lat'] + y * lat_step + lat_step/2, 6),
                            "count": count
                        })
        else:
            for hour in range(24):
                hour_data = heatmap[hour]
                for x in range(lng_size):
                    for y in range(lat_size):
                        count = int(hour_data[x, y])
                        if count > 0:
                            result.append({
                                "lng": round(BEIJING_BOUNDS['min_lng'] + x * lng_step + lng_step/2, 6),
                                "lat": round(BEIJING_BOUNDS['min_lat'] + y * lat_step + lat_step/2, 6),
                                "count": count,
                                "hour": hour
                            })

        return jsonify({
            "status": "success",
            "data": result,
            "process_time": round(time.time() - start_time, 2),
            "grid_size": grid_size
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "process_time": round(time.time() - start_time, 2)
        }), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True, port=5000)
