# Git Sync 开发进度

## 已完成功能

### 核心功能
- [x] CLI 命令行工具
  - [x] `git-sync init` - 初始化项目
  - [x] `git-sync key` - SSH 密钥管理（gen/list/show/delete）
  - [x] `git-sync repo list` - 列出仓库
  - [x] `git-sync sync` - 同步仓库

- [x] 配置管理
  - [x] 多配置文件支持（configs/ 目录）
  - [x] YAML 配置加载和合并
  - [x] 配置写入功能

- [x] SSH 密钥管理
  - [x] 密钥生成（ed25519/rsa/ecdsa）
  - [x] 密钥存储和权限管理
  - [x] 密钥清单（keys_manifest.yaml）

- [x] 同步功能
  - [x] 镜像缓存加速
  - [x] 快进检查（安全同步）
  - [x] 分支和标签同步
  - [x] 试运行模式

### Web 前端（v1.0）
- [x] 后端 API
  - [x] FastAPI 应用框架
  - [x] 配置读写 API（GET/PUT /api/config）
  - [x] 仓库 CRUD API（/api/repositories）
  - [x] 仓库排序 API（PUT /api/repositories/order）
  - [x] SSH 密钥管理 API（/api/keys）
  - [x] 同步操作 API（/api/sync）

- [x] 前端界面
  - [x] Vue 3 + Vite 项目结构
  - [x] Dashboard 概览页面
  - [x] 仓库列表页（拖拽排序）
  - [x] 仓库创建/编辑表单
  - [x] SSH 密钥管理页
  - [x] 全局设置页
  - [x] Toast 通知反馈

- [x] 同步历史记录
  - [x] 后端历史存储（JSON 文件）
  - [x] 历史 API（GET/DELETE /api/history）
  - [x] 统计 API（/api/history/stats）
  - [x] 前端历史页面
  - [x] 导航栏添加 History 链接

- [x] 定时同步功能
  - [x] 后台调度器（APScheduler）
  - [x] 调度器状态 API（/api/scheduler）
  - [x] 调度器控制 API（start/stop/reload/run）
  - [x] 前端设置页配置 UI
  - [x] 配置持久化

- [x] Docker 部署
  - [x] Dockerfile（多阶段构建）
  - [x] docker-compose.yml（开发配置）
  - [x] docker-compose.prod.yml（生产配置）
  - [x] .dockerignore

## 待开发功能

### 优先级高
- [ ] 同步失败通知（邮件/ webhook）

### 优先级中
- [ ] 用户认证（内网可选）
- [ ] 同步进度实时显示
- [ ] 仓库详情页（查看分支/标签）
- [ ] 批量操作

### 优先级低
- [ ] 暗色主题
- [ ] 多语言支持
