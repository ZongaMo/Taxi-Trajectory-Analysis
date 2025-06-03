from flask import Flask, request, jsonify
import os
import math
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from coordTransform_utils import wgs84_to_gcj02
from datetime import datetime
import time

app = Flask(__name__)

# 预分配内存的数据结构
class SpatialIndex:
    __slots__ = ['min_lng', 'max_lng', 'min_lat', 'max_lat', 'grid_size', 'cols', 'rows']
    
    def __init__(self, area, grid_size=0.01):
        self.min_lng, self.max_lng, self.min_lat, self.max_lat = area
        self.grid_size = grid_size
        self.cols = math.ceil((self.max_lng - self.min_lng) / grid_size)
        self.rows = math.ceil((self.max_lat - self.min_lat) / grid_size)



def process_file_optimized(args):
    """优化后的文件处理函数"""
    filename, area1, area2, flow_stats = args
        
    # 提前计算区域边界
    a1_min_lng, a1_max_lng, a1_min_lat, a1_max_lat = area1
    a2_bounds = area2 if area2 else None
    
    with open(filename, 'r') as file:
        current_taxi = None
        prev_in_a1 = False
        prev_in_a2 = False
        prev_hour = None
        
        for line in file:
            # 使用快速分割方法
            parts = line.split(',', 3)
            if len(parts) < 4:
                continue
            
            try:
                taxi_id = parts[0]
                time_part = parts[1][11:13]  # 直接提取小时部分
                hour = int(time_part)
                lng = float(parts[2])
                lat = float(parts[3])
                
                # 坐标转换
                lng, lat = wgs84_to_gcj02(lng, lat)
                
                # 状态检查
                if taxi_id != current_taxi:
                    current_taxi = taxi_id
                    prev_in_a1 = False
                    prev_in_a2 = False
                    prev_hour = None
                
                # 区域判断（使用短路计算加速）
                in_a1 = (a1_min_lng <= lng <= a1_max_lng) and (a1_min_lat <= lat <= a1_max_lat)
                in_a2 = False
                if a2_bounds:
                    a2_min_lng, a2_max_lng, a2_min_lat, a2_max_lat = a2_bounds
                    in_a2 = (a2_min_lng <= lng <= a2_max_lng) and (a2_min_lat <= lat <= a2_max_lat)
                
                # 状态转移检测
                if prev_hour == hour:
                    if a2_bounds:
                        # 双区域模式
                        if prev_in_a1 and in_a2:
                            flow_stats[hour][1] += 1  # flowOut
                        elif prev_in_a2 and in_a1:
                            flow_stats[hour][0] += 1  # flowIn
                    else:
                        # 单区域模式
                        if not prev_in_a1 and in_a1:
                            flow_stats[hour][0] += 1  # flowIn
                        elif prev_in_a1 and not in_a1:
                            flow_stats[hour][1] += 1  # flowOut
                
                prev_in_a1 = in_a1
                prev_in_a2 = in_a2
                prev_hour = hour
            
            except (ValueError, IndexError):
                continue

        

@app.route('/flow_analysis', methods=['GET'])
def analyze_flow():
    """优化后的API端点"""
    try:
        start_time = time.time()
        
        # 参数解析
        area1 = tuple(map(float, request.args['area1'].split(',')))
        area2 = tuple(map(float, request.args.get('area2', '').split(','))) if 'area2' in request.args else None
        folder_path = request.args.get('folder_path', 'taxi_log_2008_by_id')
        
        # 创建共享内存
        flow_array = np.zeros((24, 2), dtype=np.int32)
        
        try:
            # 准备任务
            files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                    if f.endswith('.txt')]
            args = [(f, area1, area2, flow_array) for f in files]
            
            # 并行处理（使用imap_unordered减少内存占用）
            with ThreadPoolExecutor(max_workers=5000) as executor:
                executor.map(process_file_optimized, args)
            
            # 生成响应
            output = []
            for hour in range(24):
                output.append({
                    "hour": hour,
                    "flowIn": int(flow_array[hour][0]),
                    "flowOut": int(flow_array[hour][1]),
                    "netFlow": int(flow_array[hour][0] - flow_array[hour][1])
                })
            
            return jsonify({
                "status": "success",
                "processingTime": round(time.time() - start_time, 2),
                "data": output,
                "params": {
                    "area1": area1,
                    "area2": area2 if area2 else None,
                }
            })
        except Exception as e:
            raise e
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=False, processes=1)
