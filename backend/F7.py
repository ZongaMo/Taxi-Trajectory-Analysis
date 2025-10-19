import datetime

from flask import Flask, request, jsonify
import sqlite3
import math
from collections import defaultdict, Counter
import coordTransform_utils

import os
app = Flask(__name__)
# 数据库路径，从环境变量读取
DB_PATH = os.environ.get('DB_PATH', "trajectory.db")

def transform_wgs84_to_gcj02_point(lng, lat):
    lng_gcj, lat_gcj = coordTransform_utils.wgs84_to_gcj02(lng, lat)
    return lng_gcj, lat_gcj
# 经纬度转换为大致距离（单位：米）
def haversine(lat1, lng1, lat2, lng2):
    """
    使用Haversine公式计算两个经纬度点之间的距离

    参数：
        lat1 (float): 第一个点的纬度
        lng1 (float): 第一个点的经度
        lat2 (float): 第二个点的纬度
        lng2 (float): 第二个点的经度

    返回：
        float: 两点之间的距离（单位：米）
    """
    R = 6371000  # 地球半径，单位米
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def path_distance(trail):
    """
    计算轨迹的总距离

    参数：
        trail (list): 轨迹点列表，每个点包含lat和lng字段

    返回：
        float: 轨迹的总距离（单位：米）
    """
    total = 0
    for i in range(1, len(trail)):
        total += haversine(trail[i-1]['lat'], trail[i-1]['lng'], trail[i]['lat'], trail[i]['lng'])
    return total

# 网格化轨迹编码（简化聚类）
def encode_path(trail, grid_size=0.001):
    """
    对轨迹进行网格化编码

    参数：
        trail (list): 轨迹点列表
        grid_size (float): 网格大小，默认0.001

    返回：
        tuple: 网格化编码后的轨迹
    """
    return tuple((round(p['lat']/grid_size), round(p['lng']/grid_size)) for p in trail)

@app.route('/frequent_paths', methods=['POST'])
def frequent_paths():
    """
    处理频繁路径查询请求

    请求参数（JSON）：
        {
            "minDistance": 最小距离（单位：米，默认1000）,
            "k": 返回的Top-K路径数量（默认5）
        }

    返回：
        JSON响应：包含最频繁路径的JSON对象
    """
    req = request.get_json()
    min_distance = req.get("minDistance", 1000)  # 单位：米
    top_k = req.get("k", 5)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT taxi_id, time, lng, lat FROM traj_data ORDER BY taxi_id, time")
    rows = cursor.fetchall()
    conn.close()

    current_id = None
    current_trail = []

    path_counter = Counter()
    path_samples = {}

    def add_trail_if_valid(trail):
        if len(trail) >= 2 and path_distance(trail) >= min_distance:
            key = encode_path(trail)
            path_counter[key] += 1
            if key not in path_samples:
                path_samples[key] = trail[:]

    for taxi_id, time, lng, lat in rows:
        lng_gcj, lat_gcj = transform_wgs84_to_gcj02_point(lng, lat)
        point = {"lat": lat_gcj, "lng": lng_gcj, "time": time}
        # point = [lat_gcj, lng_gcj, datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S").timestamp()]

        if taxi_id != current_id:
            add_trail_if_valid(current_trail)
            current_trail = [point]
            current_id = taxi_id
        else:
            current_trail.append(point)

    # 处理最后一个轨迹
    add_trail_if_valid(current_trail)

    # 获取 Top-K
    top_paths = path_counter.most_common(top_k)

    result = []
    for path_key, count in top_paths:
        sample_trail = path_samples[path_key]
        result.append({
            "vender": count,
            "path": [[
                p['lat'],
                p['lng'],
                datetime.datetime.strptime(p['time'],"%Y-%m-%d %H:%M:%S").timestamp()
            ] for p in sample_trail]
        })

    return jsonify({
        "total": len(path_counter),
        "topK": top_k,
        "result": result
    })
if __name__ == '__main__':
    app.run(debug=True)

