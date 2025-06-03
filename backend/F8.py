"""
出租车轨迹分析模块

该模块提供基于Flask的Web服务，用于分析出租车在两个指定区域之间的频繁路径。
"""
import datetime

from flask import Flask, request, jsonify
import sqlite3
import math
from collections import defaultdict, Counter
import coordTransform_utils


# 初始化Flask应用
app = Flask(__name__)

# 数据库路径
DB_PATH = "trajectory.db"

def point_in_rect(lng, lat, lt, rb):
    """
    判断点是否在矩形区域内

    参数:
        lng (float): 经度
        lat (float): 纬度
        lt (list): 矩形左上角坐标 [经度, 纬度]
        rb (list): 矩形右下角坐标 [经度, 纬度]

    返回:
        bool: 如果点在矩形区域内返回True，否则返回False
    """
    return lt[0] <= lng <= rb[0] and rb[1] <= lat <= lt[1]

def transform_wgs84_to_gcj02_point(lng, lat):
    return coordTransform_utils.wgs84_to_gcj02(lng, lat)

def transform_gcj02_to_wgs84_point(lng, lat):
    return coordTransform_utils.gcj02_to_wgs84(lng, lat)
    
def encode_path(trail, grid_size=0.001):
    """
    对轨迹进行网格化编码

    参数:
        trail (list): 轨迹点列表，每个点包含lat和lng字段
        grid_size (float): 网格大小，默认0.001

    返回:
        tuple: 网格化编码后的轨迹
    """
    return tuple((round(p['lat']/grid_size), round(p['lng']/grid_size)) for p in trail)

@app.route('/frequent_paths_ab', methods=['POST'])
def frequent_paths_ab():
    """
    处理频繁路径查询请求

    请求参数（JSON）:
        {
            "areaA": {
                "ltPoint": [经度, 纬度],  # 区域A左上角
                "rbPoint": [经度, 纬度]   # 区域A右下角
            },
            "areaB": {
                "ltPoint": [经度, 纬度],  # 区域B左上角
                "rbPoint": [经度, 纬度]   # 区域B右下角
            },
            "k": 返回的Top-K路径数量（默认5）
        }

    返回:
        JSON响应：包含最频繁路径的JSON对象
    """
    req = request.get_json()
    areaA = req.get("areaA")
    areaB = req.get("areaB")
    top_k = req.get("k", 5)

    # 验证输入参数
    if not areaA or not areaB:
        return jsonify({"error": "Missing areaA or areaB"}), 400
        
    ltA_wgs = transform_gcj02_to_wgs84_point(*areaA["ltPoint"])
    rbA_wgs = transform_gcj02_to_wgs84_point(*areaA["rbPoint"])
    ltB_wgs = transform_gcj02_to_wgs84_point(*areaB["ltPoint"])
    rbB_wgs = transform_gcj02_to_wgs84_point(*areaB["rbPoint"])

    # 连接数据库并查询所有轨迹数据
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT taxi_id, time, lng, lat FROM traj_data ORDER BY taxi_id, time")
    rows = cursor.fetchall()
    conn.close()

    # 初始化统计变量
    path_counter = Counter()  # 用于统计路径出现次数
    path_samples = {}  # 用于存储路径样本

    # 初始化轨迹处理变量
    current_id = None  # 当前处理的出租车ID
    insideA = False  # 标记是否进入区域A
    segment = []  # 当前处理的路径段

    # 遍历所有轨迹点
    def add_path_if_valid(trail):
        if len(trail) >= 2:
            key = encode_path(trail)
            path_counter[key] += 1
            if key not in path_samples:
                path_samples[key] = trail[:]

    for taxi_id, time, lng_wgs, lat_wgs in rows:
        if taxi_id != current_id:
            current_id = taxi_id
            insideA = False
            segment = []

        if not insideA and point_in_rect(lng_wgs, lat_wgs, ltA_wgs, rbA_wgs):
            insideA = True
            segment = []

        if insideA:
            lng_gcj, lat_gcj = transform_wgs84_to_gcj02_point(lng_wgs, lat_wgs)
            segment.append({
                "lat": lat_gcj,
                "lng": lng_gcj,
                "time": time
            })

            if point_in_rect(lng_wgs, lat_wgs, ltB_wgs, rbB_wgs):
                add_path_if_valid(segment)
                insideA = False
                segment = []


    # 获取出现次数最多的前K条路径
    top_paths = path_counter.most_common(top_k)

    # 构建响应数据
    response = []
    for path_key, count in top_paths:
        path=path_samples[path_key]
        response.append({
            "path":[[
                p['lat'],
                p['lng'],
                datetime.datetime.strptime(p['time'],"%Y-%m-%d %H:%M:%S").timestamp()
            ] for p in path]
        })

    # 返回JSON响应
    return jsonify({
        "total": len(path_counter),  # 总路径数
        "topK": top_k,  # 请求的Top-K值
        "result": response  # 最频繁路径列表
    })
if __name__ == '__main__':
    app.run(debug=True)
