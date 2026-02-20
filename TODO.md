# Git Sync TODO List

## 任务 1: Docker 化部署

### 1.1 创建 Dockerfile
- [ ] 基于 Python 3.12 slim 镜像
- [ ] 安装 git 和 openssh-client 依赖
- [ ] 配置工作目录和环境变量
- [ ] 复制项目文件并安装依赖
- [ ] 配置入口点脚本

### 1.2 创建 docker-compose.yml
- [ ] 定义服务配置
- [ ] 配置卷挂载（配置文件、SSH密钥、mirror缓存）
- [ ] 设置环境变量
- [ ] 配置网络和重启策略

### 1.3 定时任务配置
- [ ] 方案选择：容器内 crontab vs 外部调度器
- [ ] 创建定时同步脚本
- [ ] 配置日志输出
- [ ] 添加健康检查

### 1.4 Docker 辅助文件
- [ ] 创建 .dockerignore
- [ ] 创建 entrypoint.sh
- [ ] 编写 Docker 部署文档

---

## 任务 2: Web 前端配置页面

### 2.1 后端 API 开发
- [ ] 选择 Web 框架（Flask/FastAPI）
- [ ] 创建 API 路由结构
  - [ ] `GET /api/config` - 获取当前配置
  - [ ] `PUT /api/config` - 更新配置
  - [ ] `GET /api/repositories` - 获取仓库列表
  - [ ] `POST /api/repositories` - 创建新仓库配置
  - [ ] `PUT /api/repositories/{name}` - 更新仓库配置
  - [ ] `DELETE /api/repositories/{name}` - 删除仓库配置
  - [ ] `GET /api/keys` - 获取 SSH 密钥列表
  - [ ] `POST /api/keys` - 生成新密钥
  - [ ] `DELETE /api/keys/{name}` - 删除密钥
  - [ ] `POST /api/sync` - 触发同步
  - [ ] `GET /api/sync/status` - 获取同步状态/历史

### 2.2 前端页面开发
- [ ] 选择前端方案（纯 HTML/JS 或 Vue/React）
- [ ] 创建页面布局
  - [ ] 仓库配置管理页面
  - [ ] SSH 密钥管理页面
  - [ ] 同步操作页面
  - [ ] 日志查看页面
- [ ] 实现仓库排序功能（拖拽排序）
- [ ] 实现新建/编辑/删除仓库表单
- [ ] 实现配置保存和验证

### 2.3 集成与部署
- [ ] 配置静态文件服务
- [ ] 添加用户认证（可选）
- [ ] 更新 docker-compose 集成 Web 服务
- [ ] 编写 Web 模块使用文档

---

## 优先级建议

| 优先级 | 任务 | 复杂度 |
|--------|------|--------|
| P0 | 1.1 Dockerfile | 低 |
| P0 | 1.2 docker-compose.yml | 低 |
| P1 | 1.3 定时任务配置 | 中 |
| P1 | 2.1 后端 API | 中-高 |
| P2 | 2.2 前端页面 | 中-高 |
| P2 | 2.3 集成部署 | 中 |

---

## 技术选型建议

### Docker 定时任务
- **推荐方案**: 使用外部调度器（如 Kubernetes CronJob 或宿主机 crontab 调用 `docker compose run`）
- **备选方案**: 容器内运行 cron daemon

### Web 框架
- **推荐**: FastAPI（自动生成 API 文档，异步支持，类型提示）
- **备选**: Flask（更轻量，学习曲线低）

### 前端
- **推荐**: Vue 3 + Vite（轻量，易上手）
- **备选**: 纯 HTML + Alpine.js（最简单，无需构建）
