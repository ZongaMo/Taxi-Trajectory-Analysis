const express = require("express");
const cors = require("cors");
const { createProxyMiddleware } = require("http-proxy-middleware");
const path = require("path");
// const sqlite3 = require("sqlite3").verbose();
const app = express();
const port = 3000;
const backendUrl = "http://localhost:5000"; // 后端API地址

app.use(express.json()); // 解析JSON请求体
// 1. 静态文件服务（指向打包后的dist目录）
app.use(express.static(path.join(__dirname, "dist")));
app.use(cors());
// 2. API代理（将/api前缀的请求转发到后端）
app.use(
  "/api",
  createProxyMiddleware({
    target: backendUrl,
    changeOrigin: true,
    pathRewrite: { "^/api": "" }, // 去除请求路径中的/api前缀
    logLevel: "debug",
    onProxyRes: (proxyRes) => {
      proxyRes.headers["Access-Control-Allow-Origin"] = "*";
      proxyRes.headers["Access-Control-Allow-Credentials"] = "true";
    },
    // 增加错误处理，防止代理过程中出现错误导致服务器崩溃
    onError: function (err, req, res) {
      console.error("代理请求发生错误:", err);
      res.status(500).send("代理请求发生错误");
    },
  })
);

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});

app.use((req, res, next) => {
  console.log(`收到请求: ${req.method} ${req.url}`);
  next(); // 传递给下一个中间件
});
