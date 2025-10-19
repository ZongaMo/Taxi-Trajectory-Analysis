from flask import Flask, request, jsonify
import os
import math
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor
from coordTransform_utils import wgs84_to_gcj02
import time
import csv  # 新增导入

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

def create_heatmap(grid_size=0.01):
    """创建热力图网格（修正维度问题）"""
    lng_size = int((BEIJING_BOUNDS['max_lng'] - BEIJING_BOUNDS['min_lng']) / grid_size) + 1
    lat_size = int((BEIJING_BOUNDS['max_lat'] - BEIJING_BOUNDS['min_lat']) / grid_size) + 1
    heatmap = np.zeros((24, lng_size, lat_size), dtype=np.int32)
    return heatmap, (lng_size, lat_size)

def process_file_optimized(args):
    """优化后的文件处理函数"""
    filename, folder_path, grid_size, heatmap, grid_dims = args
    lng_size, lat_size = grid_dims
    
    with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
        reader = csv.reader(file)  # 使用 csv.reader 替代手动分割
        for parts in reader:
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
                continue

@app.route('/api/heatmap', methods=['POST'])
def get_optimized_heatmap():
    """优化后的热力图端点"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        grid_size = float(data.get('grid_width', 0.01))
        target_hour = int(data['hour']) if 'hour' in data else None
        folder_path = data.get('folder_path', 'taxi_log_2008_by_id')
        
        heatmap, grid_dims = create_heatmap(grid_size)
        lng_size, lat_size = grid_dims
        
        files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
        print(f"Processing {len(files)} files...")
        
        # 调整线程池的最大线程数
        max_workers = min(32, len(files))  # 根据文件数动态调整线程数
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(process_file_optimized,
                         [(f, folder_path, grid_size, heatmap, grid_dims) for f in files])
        
        result = []
        lng_step = grid_size
        lat_step = grid_size
        
        if target_hour is not None:
            hour_data = heatmap[target_hour]
            non_zero_indices = np.argwhere(hour_data > 0)  # 使用 NumPy 查找非零元素
            for x, y in non_zero_indices:
                count = int(hour_data[x, y])
                result.append({
                    "lng": round(BEIJING_BOUNDS['min_lng'] + x * lng_step + lng_step/2, 6),
                    "lat": round(BEIJING_BOUNDS['min_lat'] + y * lat_step + lat_step/2, 6),
                    "count": count
                })
        else:
            for hour in range(24):
                hour_data = heatmap[hour]
                non_zero_indices = np.argwhere(hour_data > 0)
                for x, y in non_zero_indices:
                    count = int(hour_data[x, y])
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
    app.run(host='0.0.0.0', debug=True, port=5000)
