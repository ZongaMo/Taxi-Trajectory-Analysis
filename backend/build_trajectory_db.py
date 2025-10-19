import os
import sqlite3
import datetime

# 从环境变量读取路径，默认使用当前目录
DATA_DIR = os.environ.get('DATA_DIR', r".\\taxi_log_2008_by_id")
DB_PATH = os.environ.get('DB_PATH', "trajectory.db")

def parse_line(line):
    parts = line.strip().split(',')
    if len(parts) != 4:
        return None
    try:
        return {
            "id": parts[0],
            "time": parts[1],
            "lng": float(parts[2]),
            "lat": float(parts[3])
        }
    except:
        return None

def build_database():
    print("初始化数据库...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS traj_data")
    cursor.execute("DROP TABLE IF EXISTS traj_index")

    cursor.execute("""
        CREATE TABLE traj_data (
            point_id INTEGER PRIMARY KEY AUTOINCREMENT,
            taxi_id TEXT,
            time TEXT,
            lng REAL,
            lat REAL
        )
    """)

    cursor.execute("""
        CREATE VIRTUAL TABLE traj_index USING rtree(
            point_id,
            min_lng, max_lng,
            min_lat, max_lat
        )
    """)

    conn.commit()

    print("开始导入轨迹数据...")

    count = 0
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".txt"):
            continue
        taxi_id = filename.replace(".txt", "")
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, 'r') as f:
            for line in f:
                record = parse_line(line)
                if not record:
                    continue
                cursor.execute("INSERT INTO traj_data (taxi_id, time, lng, lat) VALUES (?, ?, ?, ?)",
                               (taxi_id, record['time'], record['lng'], record['lat']))
                point_id = cursor.lastrowid
                # 插入空间索引
                cursor.execute("INSERT INTO traj_index VALUES (?, ?, ?, ?, ?)",
                               (point_id, record['lng'], record['lng'], record['lat'], record['lat']))

                count += 1
                if count % 100000 == 0:
                    print(f"已处理 {count} 条轨迹点...")
                    conn.commit()
    conn.commit()
    print("构建完成，总计轨迹点数：", count)
    conn.close()

if __name__ == "__main__":
    build_database()
