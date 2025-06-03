# from flask import Flask
# from F1 import get_trail_lists,get_trails_post
# from F3 import query_region
# from F4 import get_optimized_heatmap
# from F56 import analyze_flow
# from F7 import frequent_paths
# from F8 import frequent_paths_ab
# from F9 import analyze_shortest_path

import flask
import F1
import F3
import F4
import F56
import F7
import F8
import F9
# import flask_sWerkzeug pkg_resources不支持作为API使用ocketio

import time
app = flask.Flask(__name__)

@app.before_request
def log_request_start():
    print(f"收到 {flask.request.method} 请求，请求路径: {flask.request.path}")

@app.after_request
def log_request_end(response):
    print(f"响应时间: {time.time() - flask.g.start_time:.4f} 秒")
    return response

@app.before_request
def start_timer():
    flask.g.start_time = time.time()

# F1
@app.route('/trailLists', methods=['GET'])
def new_get_trail_lists():
    return F1.get_trail_lists()

@app.route('/trails/data', methods=['POST'])
def new_get_trails_post():
    return F1.get_trails_post()

# F3
@app.route('/query_region', methods=['POST'])
def new_query_region():
    return F3.query_region()


# F4
@app.route('/heatmap', methods=['POST'])
def new_get_optimized_heatmap():
    return F4.get_optimized_heatmap()

# F56
@app.route('/flow_analysis', methods=['GET'])
def new_analyze_flow():
    return F56.analyze_flow()

# F7
@app.route('/frequent_paths', methods=['POST'])
def new_frequent_paths():
    return F7.frequent_paths()

# F8
@app.route('/frequent_paths_ab', methods=['POST'])
def new_frequent_paths_ab():
    return F8.frequent_paths_ab()

# F9
@app.route('/optimized_path', methods=['GET'])
def new_analyze_shortest_path():
    return F9.analyze_shortest_path()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    input("please input any key to exit!")