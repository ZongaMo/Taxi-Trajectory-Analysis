from flask import Flask, request, jsonify
import os
from datetime import datetime
from multiprocessing import Pool, cpu_count, Manager
from coordTransform_utils import wgs84_to_gcj02
import time

app = Flask(__name__)

class TrajectoryAnalyzer:
    __slots__ = ['hour', 'entry_time', 'exit_time', 'path']
    
    def __init__(self, hour=None):
        self.hour = hour
        self.entry_time = None
        self.exit_time = None
        self.path = []

def parse_timestamp(time_str):
    """安全解析时间戳"""
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def process_trajectory(args):
    """健壮的轨迹处理函数"""
    filename, area1, area2, target_hour, result_dict = args
    local_stats = {}
    
    try:
        with open(filename, 'r') as f:
            current_taxi = None
            analyzer = None
            
            for line in f:
                parts = line.strip().split(',', 3)
                if len(parts) < 4:
                    continue
                
                try:
                    taxi_id = parts[0]
                    time_str = parts[1]
                    lng, lat = wgs84_to_gcj02(float(parts[2]), float(parts[3]))
                    hour = int(time_str[11:13])
                    
                    # 时间过滤
                    if target_hour is not None and hour != target_hour:
                        continue
                    
                    if taxi_id != current_taxi:
                        if analyzer is not None:  # 明确检查None
                            update_stats(analyzer, local_stats)
                        current_taxi = taxi_id
                        analyzer = TrajectoryAnalyzer(hour)
                    
                    # 确保analyzer已初始化
                    if analyzer is None:
                        continue
                    
                    # 区域判断
                    in_area1 = (area1[0] <= lng <= area1[1]) and (area1[2] <= lat <= area1[3])
                    in_area2 = (area2[0] <= lng <= area2[1]) and (area2[2] <= lat <= area2[3])
                    
                    if not analyzer.path and in_area1:
                        analyzer.entry_time = parse_timestamp(time_str)
                        if analyzer.entry_time:  # 时间解析成功
                            analyzer.path.append((lng, lat))
                    elif analyzer.path:
                        analyzer.path.append((lng, lat))
                        if in_area2:
                            analyzer.exit_time = parse_timestamp(time_str)
                            if analyzer.exit_time:  # 时间解析成功
                                update_stats(analyzer, local_stats)
                            analyzer = None
                
                except (ValueError, IndexError):
                    continue
            
            # 最终检查未处理的轨迹
            if analyzer is not None and analyzer.path:
                update_stats(analyzer, local_stats)
    
    except Exception as e:
        print(f"处理文件 {filename} 时出错: {str(e)}")
    
    # 合并结果
    for hour, stats in local_stats.items():
        if hour not in result_dict or stats['time'] < result_dict[hour]['time']:
            result_dict[hour] = stats

def update_stats(analyzer, stats_dict):
    """安全更新统计结果"""
    if (analyzer is not None and analyzer.path and 
        analyzer.entry_time and analyzer.exit_time):
        travel_time = (analyzer.exit_time - analyzer.entry_time).total_seconds() / 60
        hour = analyzer.hour
        
        if hour not in stats_dict or travel_time < stats_dict[hour]['time']:
            stats_dict[hour] = {
                'path': analyzer.path.copy(),
                'time': round(travel_time, 2),  # 保留2位小数
                'count': 1
            }
        elif travel_time == stats_dict[hour]['time']:
            stats_dict[hour]['count'] += 1

@app.route('/api/shortest_path', methods=['GET'])
def analyze_shortest_path():
    """健壮的API端点"""
    start_time = time.time()
    
    try:
        # 参数验证
        area1 = tuple(map(float, request.args['area1'].split(',')))
        area2 = tuple(map(float, request.args['area2'].split(',')))
        target_hour = int(request.args['hour']) if 'hour' in request.args else None
        folder_path = request.args.get('folder_path', 'GO')
        
        # 坐标转换
        def convert_area(area):
            min_lng, max_lng, min_lat, max_lat = area
            return (
                wgs84_to_gcj02(min_lng, min_lat)[0],
                wgs84_to_gcj02(max_lng, max_lat)[0],
                wgs84_to_gcj02(min_lng, min_lat)[1],
                wgs84_to_gcj02(max_lng, max_lat)[1]
            )
        
        area1 = convert_area(area1)
        area2 = convert_area(area2)
        
        # 并行处理
        with Manager() as manager:
            result_dict = manager.dict()
            files = [os.path.join(folder_path, f) 
                    for f in os.listdir(folder_path) 
                    if f.endswith('.txt')]
            
            workers = min(cpu_count(), 4)
            with Pool(workers) as pool:
                pool.map(process_trajectory,
                        [(f, area1, area2, target_hour, result_dict) for f in files],
                        chunksize=5)
            
            # 构建响应
            response_data = []
            if target_hour is not None:
                stats = result_dict.get(target_hour, {'path': None, 'time': -1, 'count': 0})
                response_data.append({
                    "hour": target_hour,
                    "path": stats['path'],
                    "travel_time": stats['time'],
                    "sample_count": stats['count']
                })
            else:
                for hour in range(24):
                    stats = result_dict.get(hour, {'path': None, 'time': -1, 'count': 0})
                    response_data.append({
                        "hour": hour,
                        "path": stats['path'],
                        "travel_time": stats['time'],
                        "sample_count": stats['count']
                    })
            
            return jsonify({
                "status": "success",
                "data": response_data,
                "process_time": round(time.time() - start_time, 2)
            })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "process_time": round(time.time() - start_time, 2)
        }), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True, port=5000)
