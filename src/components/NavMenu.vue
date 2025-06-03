<template>
  <div class="nav-float">
    <el-menu
      :default-active="activeIndex"
      class="el-menu-demo"
      mode="horizontal"
      background-color="#fff"
      text-color="#303133"
      active-text-color="#409EFF"
      @select="handleSelect"
      router
    >
      <el-menu-item
        v-for="item in menuItems"
        :key="item.index"
        :index="item.index"
      >
        <i :class="item.icon" v-if="item.icon"></i>
        <span slot="title">{{ item.label }}</span>
      </el-menu-item>
    </el-menu>
    <div
      style="
        position: fixed;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        top: 24px;
        right: 32px;
        z-index: 9999;
        width: 35%;
      "
    >
      <el-select
        v-model="selectedOptions"
        multiple
        filterable
        remote
        reserve-keyword
        collapse-tags
        clearable
        :remote-method="remoteMethod"
        placeholder="请输入id"
        v-show="this.activeIndex === '/'"
      >
        <el-option
          v-for="item in options"
          :key="item"
          :label="item"
          :value="item"
        />
      </el-select>
      <el-button
        :loading="this.loading"
        type="primary"
        v-show="this.activeIndex === '/'"
        @click="handleSearch"
      >
        确定
      </el-button>
    </div>
  </div>
</template>

<script>
import axios from "axios";
export default {
  name: "NavMenu",
  data() {
    return {
      activeIndex: this.$route.path,
      selectedOptions: [], // 选中的选项
      options: [], // 关键字匹配结果
      menuItems: [
        { index: "/", label: "轨迹展示", icon: "el-icon-s-promotion" },
        { index: "/density", label: "车流密度", icon: "el-icon-s-flag" },
        { index: "/analysis", label: "工具分析", icon: "el-icon-s-data" },
      ],
    };
  },
  watch: {
    "$route.path"(newPath) {
      this.activeIndex = newPath;
    },
  },
  computed: {
    loading() {
      return this.$store.state.trails.loading;
    },
  },
  methods: {
    handleSelect(key) {
      this.activeIndex = key;
      this.$emit("menu-select", key);
    },
    handleSearch() {
      var simplify = false;
      if (this.selectedOptions.length === 0) {
        this.selectedOptions = "all";
        // simplify = true;
      }
      this.$store.dispatch("fetchTrails", {
        taxi_ids: this.selectedOptions,
        simplify: simplify,
        tolerance: 0.0001,
      });
    },
    // 定义防抖后的远程方法
    remoteMethod(queryString) {
      // 定义防抖定时器
      let timer = null;
      // 清除之前的定时器
      if (timer) {
        clearTimeout(timer);
      }
      // 如果查询字符串为空，不发送请求
      // if (!queryString) {
      //   this.options = [];
      //   return;
      // }
      // 设置新的定时器
      timer = setTimeout(() => {
        // 发起get请求
        axios
          .get("/api/trailLists", {
            params: {
              keyword: queryString,
            },
          })
          .then((response) => {
            this.options = response.data;
          })
          .catch((error) => {
            console.error("获取轨迹列表失败:", error);
          });
      }, 400);
    },
  },
};
</script>

<style scoped>
.nav-float {
  position: fixed;
  top: 24px;
  left: 32px;
  z-index: 1500;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  /* border-radius: 12px; */
}
.el-menu-demo {
  border-radius: 6px;
  /* min-width: 480px; */
}
</style>
