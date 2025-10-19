# Docker部署说明

本项目使用Docker容器化部署，实现了前后端分离的架构。为了优化Docker镜像大小，我们将数据文件分离到单独的volume中。

## 部署准备

1. 确保已安装Docker和Docker Compose
2. 下载出租车轨迹数据文件（taxi_log_2008_by_id目录下的txt文件）

## 部署步骤

### 1. 准备数据

在部署前，需要将数据文件放入数据卷中。有两种方式：

#### 方式一：使用本地目录映射（推荐）

修改`docker-compose.yml`文件，将volume改为绑定挂载：

```yaml
volumes:
  taxi_data:
    driver: local
    driver_opts:
      type: 'none'
      o: 'bind'
      device: '/本地路径/taxi_data'
```

然后在本地路径创建数据目录结构：

```
taxi_data/
  taxi_log_2008_by_id/
    # 放入所有轨迹数据txt文件
```

#### 方式二：使用Docker volume（适合生产环境）

使用Docker volume后，可以通过以下命令将数据复制到volume中：

```bash
# 创建volume
docker volume create taxi_data

# 复制数据到volume
# 注意：需要先运行一次docker-compose up，让volume被创建
# 然后使用临时容器复制数据
docker run --rm -v taxi_data:/data -v /本地路径/taxi_log_2008_by_id:/source busybox cp -r /source/* /data/taxi_log_2008_by_id/
```

### 2. 构建数据库

在首次部署时，需要构建数据库。运行以下命令：

```bash
docker-compose --profile init run init-db
```

这个过程可能需要一些时间，取决于数据量的大小。

### 3. 启动服务

数据库构建完成后，启动整个应用：

```bash
docker-compose up -d
```

服务启动后，可以通过以下地址访问：
- 前端应用：http://localhost:80
- 后端API：http://localhost:5000

## 常用命令

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
```

### 停止服务

```bash
docker-compose down
```

### 重启服务

```bash
docker-compose restart
```

## 注意事项

1. 数据库文件存储在Docker volume中，即使容器被删除，数据也不会丢失
2. 如果需要更新数据库，只需重新运行init-db服务
3. 前端服务会自动将API请求代理到后端服务
4. 确保数据文件路径正确，且有足够的磁盘空间

## 故障排除

### 数据库连接失败

- 检查数据库是否已成功构建
- 查看后端服务日志，确认数据库路径配置正确

### 数据文件未找到

- 确认数据文件已正确放入数据卷
- 检查DATA_DIR环境变量配置

### 性能问题

- 数据库构建是一个耗时过程，请耐心等待
- 可以考虑增加Docker的资源限制以提高性能