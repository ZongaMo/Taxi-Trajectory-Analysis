<template>
  <div id="app">
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no" />
    <nav-menu @search="selectedRoutes = $event" />
    <router-view :key="this.$route.paths" id="router" />
    <map-view id="map" :selected-routes="selectedRoutes" />
  </div>
</template>

<script>
import NavMenu from "./components/NavMenu.vue";
import MapView from "./views/MapView.vue";
export default {
  name: "App",
  components: {
    NavMenu,
    MapView,
  },
  data() {
    return {
      selectedRoutes: [],
    };
  },
  methods: {},
  // watch: {
  //   selectedRoutes(newRoutes) {
  //     console.log("selectedRoutes", newRoutes);
  //   },
  // },
};
</script>
<style>
html,
body {
  margin: 0;
  padding: 0;
  overflow: hidden;
  width: 100vw;
  height: 100vh;
}
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  display: flex;
  flex-direction: row-reverse;
  height: 100vh;
}
#map {
  flex-grow: 1;
  height: 100%;
  transition: width 0.3s ease-in-out;
  min-width: calc(100vw - 600px);
}
#router {
  width: 600px;
  height: 100%;
  background-color: white;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 2000;
}
</style>
