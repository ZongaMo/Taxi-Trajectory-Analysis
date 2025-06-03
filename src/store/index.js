// 导入 Vue 框架
import Vue from "vue";
// 导入 Vuex 状态管理库
import Vuex from "vuex";
// 导入 Element UI 的 Notification 组件
import { Notification } from "element-ui";

// 让 Vue 使用 Vuex
Vue.use(Vuex);

/**
 * 创建并导出一个 Vuex 仓库实例
 * 该仓库包含状态、突变、动作和模块等部分
 */
export default new Vuex.Store({
  // 定义仓库的状态
  state: {
    map: {
      // 用于存储地图实例的状态
      map: null,
      mode: null,
      // 用于存储轨迹实例的状态
      trail: null,
      // 用于存储热力图实例的状态
      heat: null,
      // 用于存储标记点实例的状态
      markerLayer: null,
      // 用于存储矩形实例的状态
      rectangleID: null,
    },
    statistics: {
      // 用于存储出租车数量的状态
      taxiCount: "请选择",
      trafficTime: "00小时00分钟",
    },
    // 用于存储标记点的状态
    markedPoint: [],
    // 轨迹数据的状态
    trails: {
      loading: false,
      options: [],
      data: [],
    },
    refresh: false,
    echart: { visible: false, data: null },
  },
  // 定义修改状态的突变函数
  mutations: {
    /**
     * 设置地图相关状态
     * @param {Object} state - 当前状态对象
     * @param {Object} item - 包含要设置的地图属性的对象
     */
    SET_MAP(state, item) {
      for (let key in item) {
        state.map[key] = item[key];
      }
    },
    /**
     * 设置统计信息状态
     * @param {Object} state - 当前状态对象
     * @param {Object} item - 包含要设置的统计属性的对象
     */
    SET_STATISTICS(state, item) {
      for (let key in item) {
        state.statistics[key] = item[key];
      }
    },
    /**
     * 设置轨迹相关状态
     * @param {Object} state - 当前状态对象
     * @param {Object} item - 包含要设置的轨迹属性的对象
     */
    SET_TRAILS(state, item) {
      for (let key in item) {
        state.trails[key] = item[key];
      }
    },
    /**
     * 设置轨迹数据
     * @param {Object} state - 当前状态对象
     * @param {any} value - 要设置的轨迹数据
     */
    SET_TRAILS_DATA(state, value) {
      state.map.trail.setData(value);
      state.trails.data = value;
    },
    /**
     * 设置热力图数据
     * @param {Object} state - 当前状态对象
     * @param {any} value - 要设置的热力图数据
     */
    SET_HEAT_DATA(state, value) {
      console.log("设置热力图数据", value);
      // console.log("热力图实例", state.map.heat);
      state.map.heat.setData(value);
      // 数据聚合之后才能够真正获取值域范围
      state.map.heat.setShowRange(state.map.heat.getValueRange());
      state.map.map.setPitch(50).setRotation(50);
      // state.trails.data = value;
    },
    /**
     * 设置标记点
     * @param {Object} state - 当前状态对象
     * @param {Array} value - 要设置的标记点数组
     */
    SET_ECHARTS_DATA(state, value) {
      state.echart.data = value;
    },
    /**
     * 重置标记层
     * 如果存在矩形实例，则移除并重置相关状态
     * @param {Object} state - 当前状态对象
     */
    RESET_MARKERLAYER(state) {
      if (state.map.rectangleID) {
        state.map.markerLayer.remove(state.map.rectangleID);
        state.map.rectangleID = null;
        state.map.editor.setActionMode(state.map.mode.draw);
      }
    },
    SET_ECHARTS_VISIBLE(state) {
      state.echart.visible = !state.echart.visible;
    },
  },
  // 定义异步操作的动作函数
  actions: {
    /**
     * F4 异步获取热力图密度数据
     * @param {Object} param - 包含 commit 方法的对象
     * @param {Object} param2 - 包含 r 和 startTime 的参数对象
     */
    async fetchDensityData({ commit }, { r, startTime }) {
      // 设置轨迹加载状态为 true
      commit("SET_TRAILS", { loading: true });
      try {
        const params = new URLSearchParams({
          r: r / 111,
          hour: startTime,
        });
        const response = await fetch(`/api/heatmap?${params.toString()}`, {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        });
        var data = await response.json();
        if (data.length === 0) {
          // 显示暂无热力图数据的错误通知
          throw new Error("暂无热力图数据");
        } else {
          // 提交设置热力图数据的突变
          commit("SET_HEAT_DATA", data.data);
          // console.log(data);
          // 显示成功获取热力图数据的通知
          Notification({
            title: "成功",
            message: `成功获取${data.data.length}条热力图数据`,
            type: "success",
            duration: 5000,
          });
        }
      } catch (error) {
        // 显示获取热力图数据失败的错误通知
        Notification({
          title: "错误",
          message: error.message || "获取热力图数据失败",
          type: "error",
          duration: 5000,
        });
      } finally {
        // 设置轨迹加载状态为 false
        commit("SET_TRAILS", { loading: false });
      }
    },

    /**
     * F1 异步获取轨迹数据
     * @param {Object} param - 包含 commit 方法的对象
     * @param {Object} param2 - 包含 taxi_ids、simplify 和 tolerance 的参数对象
     */
    async fetchTrails({ commit }, { taxi_ids, simplify, tolerance }) {
      // 设置轨迹加载状态为 true，并记录选项
      commit("SET_TRAILS", { loading: true, options: taxi_ids });
      // console.log("正在发送路线数据...");
      try {
        // console.log(taxi_ids == "all");
        // 确保 axios 实例已正确导入和配置
        const response = await fetch("/api/trails/data", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body:
            taxi_ids === "all"
              ? JSON.stringify({
                  taxi_ids: "all",
                  sample_count: 1000,
                  simplify: simplify,
                  tolerance: tolerance,
                })
              : JSON.stringify({
                  taxi_ids: taxi_ids,
                  simplify: simplify,
                  tolerance: tolerance,
                }),
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // 提交设置轨迹数据的突变
        commit("SET_TRAILS_DATA", data);
        if (data.length === 0) {
          // 显示暂无轨迹的错误通知
          throw new Error("暂无轨迹");
        } else {
          // 显示成功获取轨迹数据的通知
          Notification({
            title: "成功",
            message: `成功获取${data.length}条轨迹`,
            type: "success",
            duration: 5000,
          });
        }
      } catch (error) {
        // 显示获取轨迹数据失败的错误通知
        Notification({
          title: "错误",
          message: error.message || "获取轨迹数据失败",
          type: "error",
          duration: 5000,
        });
      } finally {
        // 设置轨迹加载状态为 false
        commit("SET_TRAILS", { loading: false });
      }
    },
    /**
     * F3 异步获取指定区域的轨迹数据
     * @param {Object} param - 包含 commit 方法的对象
     * @param {Object} param2 - 包含 dateRange 和 area 的参数对象
     */
    async fetchAreaTrails({ commit }, { dateRange, area }) {
      // 设置轨迹加载状态为 true
      commit("SET_TRAILS", { loading: true });
      try {
        const response = await fetch("/api/query_region", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            startTime:
              dateRange[0].toISOString().split("T")[0] +
              " " +
              dateRange[0].toTimeString().split(" ")[0],
            endTime:
              dateRange[1].toISOString().split("T")[0] +
              " " +
              dateRange[1].toTimeString().split(" ")[0],
            ltPoint: [
              parseFloat(area.nw.point.lng),
              parseFloat(area.nw.point.lat),
            ],
            rbPoint: [
              parseFloat(area.se.point.lng),
              parseFloat(area.se.point.lat),
            ],
          }),
        });
        var data = await response.json();
        // console.log(data);
        if (data.total === 0) {
          // 显示查询区域范围内无轨迹的错误通知
          throw new Error("查询区域范围内无轨迹");
        } else {
          // 提交设置轨迹数据的突变
          commit("SET_TRAILS_DATA", data.path);
          // 显示成功查询区域范围内轨迹的通知
          Notification({
            title: "成功",
            message: `成功查询区域范围内${data.total}条轨迹`,
            type: "success",
            duration: 10000,
          });
        }
        // 提交设置统计信息的突变
        commit("SET_STATISTICS", { taxiCount: data.total });
      } catch (error) {
        // 显示查询区域范围内轨迹失败的错误通知
        Notification({
          title: "错误",
          message: error.message || "查询区域范围内轨迹失败",
          type: "error",
          duration: 5000,
        });
      } finally {
        // 设置轨迹加载状态为 false
        commit("SET_TRAILS", { loading: false });
      }
    },

    /**
     * F56 异步查询区域关联关系
     * @param {Object} param - 包含 commit 方法的对象
     * @param {Object} param2 - 包含 area1 和 area2 的参数对象
     */
    async fetchAreaAssociation({ commit }, { area1, area2 }) {
      // 设置轨迹加载状态为 true
      commit("SET_TRAILS", { loading: true });
      try {
        const params = {
          area1: `${area1.nw.point.lng},${area1.se.point.lng},${area1.se.point.lat},${area1.nw.point.lat}`,
        };
        if (area2) {
          params.area2 = `${area2.nw.point.lng},${area2.se.point.lng},${area2.se.point.lat},${area2.nw.point.lat}`;
        }
        const queryString = Object.entries(params)
          .map(
            ([key, value]) =>
              `${encodeURIComponent(key)}=${encodeURIComponent(value)}`
          )
          .join("&");
        const url = `/api/flow_analysis?${queryString}`;
        // console.log(url);
        const response = await fetch(url, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
        });
        var data = await response.json();
        // console.log(data);
        commit("SET_ECHARTS_DATA", data.data);
        if (data.status === "success") {
          // 显示查询区域关联关系成功的通知
          Notification({
            title: "成功",
            message: "查询区域关联关系成功",
            type: "success",
            duration: 5000,
          });
          commit("SET_ECHARTS_VISIBLE");
        } else {
          throw new Error("查询区域关联关系失败");
        }
      } catch (error) {
        // 显示查询区域关联关系失败的错误通知
        Notification({
          title: "错误",
          message: error.message || "查询区域关联关系失败",
          type: "error",
          duration: 5000,
        });
      } finally {
        // 设置轨迹加载状态为 false
        commit("SET_TRAILS", { loading: false });
      }
    },

    /**
     * F7 异步获取频繁路径数据
     * @param {Object} param - 包含 commit 方法的对象
     * @param {Object} param2 - 包含 frequence 的参数对象
     */
    async fetchFrequencePath({ commit }, { frequence }) {
      // 设置轨迹加载状态为 true
      commit("SET_TRAILS", { loading: true });
      try {
        if (!frequence.minDistance) {
          throw new Error("请输入最小距离");
        }
        const response = await fetch("/api/frequent_paths", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            minDistance: parseInt(frequence.minDistance * 1000),
            k: frequence.pathCount,
          }),
        });
        var data = await response.json();
        // console.log(data);
        this.commit("SET_TRAILS_DATA", data.result);
        Notification({
          title: "成功",
          message: "频繁路径分析成功",
          type: "success",
          duration: 5000,
        });
      } catch (error) {
        // console.error("请求 /frequent_paths 时出错:", error);
        Notification({
          title: "错误",
          message: error.message || "频繁路径分析失败",
          type: "error",
          duration: 5000,
        });
      } finally {
        // 设置轨迹加载状态为 false
        commit("SET_TRAILS", { loading: false });
      }
    },

    /**
     * F8 异步获取指定区域间的频繁路径数据
     * @param {Object} param - 包含 commit 方法的对象
     * @param {Object} param2 - 包含 frequence、area1 和 area2 的参数对象
     */
    async fetchFrequencePath2({ commit }, { frequence, area1, area2 }) {
      // 设置轨迹加载状态为 true
      commit("SET_TRAILS", { loading: true });
      try {
        const response = await fetch("/api/frequent_paths_ab", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            k: frequence.pathCount,
            areaA: {
              ltPoint: [area1.nw.point.lng, area1.nw.point.lat],
              rbPoint: [area1.se.point.lng, area1.se.point.lat],
            },
            areaB: {
              ltPoint: [area2.nw.point.lng, area2.nw.point.lat],
              rbPoint: [area2.se.point.lng, area2.se.point.lat],
            },
          }),
        });
        var data = await response.json();
        // console.log(data);
        if (data.total !== 0) {
          // 显示频繁路径分析成功的通知
          Notification({
            title: "成功",
            message: "频繁路径分析成功",
            type: "success",
            duration: 5000,
          });
          // 提交设置轨迹数据的突变
          commit("SET_TRAILS_DATA", data.result);
        } else {
          throw new Error("查询区域范围内无频繁路径");
        }
      } catch (error) {
        // console.error("请求 /flow_analysi 时出错:", error);
        // 显示频繁路径分析失败的错误通知
        Notification({
          title: "错误",
          message: error.message || "频繁路径分析失败",
          type: "error",
          duration: 5000,
        });
      } finally {
        // 设置轨迹加载状态为 false
        commit("SET_TRAILS", { loading: false });
      }
    },

    /**
     * F9 异步进行时空分析，获取通行时间
     * @param {Object} param - 包含 commit 方法的对象
     * @param {Object} param2 - 包含 area1、area2 和 hour 的参数对象
     */
    async fetchTimeSpaceAnalysis({ commit }, { area1, area2, hour }) {
      // 设置轨迹加载状态为 true
      commit("SET_TRAILS", { loading: true });
      try {
        const params = {
          area1: `${area1.nw.point.lng},${area1.se.point.lng},${area1.se.point.lat},${area1.nw.point.lat}`,
          area2: `${area2.nw.point.lng},${area2.se.point.lng},${area2.se.point.lat},${area2.nw.point.lat}`,
          hour: `${hour}`,
        };
        const queryString = Object.entries(params)
          .map(
            ([key, value]) =>
              `${encodeURIComponent(key)}=${encodeURIComponent(value)}`
          )
          .join("&");
        const url = `/api/optimized_path?${queryString}`;
        const response = await fetch(url, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
        });
        var data = await response.json();
        // console.log(data);
        if (data.status === "success") {
          // 显示通行时间分析成功的通知
          Notification({
            title: "成功",
            message: "通行时间分析成功",
            type: "success",
            duration: 5000,
          });
        } else {
          throw new Error("请求失败");
        }
        const totalMinutes = data.data[0].travel_time;

        // 提交设置统计信息的突变
        commit("SET_STATISTICS", {
          trafficTime: `${Math.floor(totalMinutes / 60)}小时
          ${Math.floor(totalMinutes % 60)}分钟`,
        });
      } catch (error) {
        // console.error("请求 /flow_analysi 时出错:", error);
        // 显示通行时间分析失败的错误通知
        Notification({
          title: "错误",
          message: error.message || "通行时间分析失败",
          type: "error",
          duration: 5000,
        });
      } finally {
        // 设置轨迹加载状态为 false
        commit("SET_TRAILS", { loading: false });
      }
    },
  },
  // 定义模块
  modules: {},
});
