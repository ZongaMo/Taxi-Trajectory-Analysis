import os
import sys
import time

# 检查数据目录是否存在
DATA_DIR = os.environ.get('DATA_DIR', './taxi_log_2008_by_id')
DB_PATH = os.environ.get('DB_PATH', 'trajectory.db')

def check_data():
    # 检查数据库文件是否存在
    if os.path.exists(DB_PATH):
        print(f"数据库文件 {DB_PATH} 已存在，可以直接使用。")
        return True
    
    # 检查数据目录是否存在
    if not os.path.exists(DATA_DIR):
        print(f"错误: 数据目录 {DATA_DIR} 不存在！")
        print("请将出租车轨迹数据文件放入数据卷中。")
        print("数据卷路径: /data (在Docker容器内)")
        print("数据文件结构应该是: /data/taxi_log_2008_by_id/*.txt")
        return False
    
    # 检查数据目录中是否有文件
    try:
        files = os.listdir(DATA_DIR)
        txt_files = [f for f in files if f.endswith('.txt')]
        
        if len(txt_files) == 0:
            print(f"错误: 数据目录 {DATA_DIR} 中没有找到txt文件！")
            print("请确保数据文件已正确放置。")
            return False
        
        print(f"找到 {len(txt_files)} 个轨迹数据文件。")
        print("注意: 数据库尚未构建。如果需要构建数据库，请运行:")
        print("python build_trajectory_db.py")
        print("这可能需要一些时间，取决于数据量的大小。")
        
    except Exception as e:
        print(f"检查数据目录时出错: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("正在检查数据...")
    check_data()
    print("数据检查完成。")