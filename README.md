# Git Sync

一个用于同步 Git 仓库的命令行工具，支持 SSH 密钥管理和安全的仓库同步。

## 功能特性

- **SSH 密钥管理**: 生成、列出、查看和删除 SSH 密钥
- **多仓库支持**: 配置文件驱动，支持批量同步多个仓库
- **安全同步**: 仅允许快进推送，避免强制覆盖目标仓库
- **分支和标签同步**: 可选择同步特定分支和标签
- **试运行模式**: 预览同步操作而不实际执行

## 安装

```bash
# 克隆仓库
git clone <repo-url>
cd github-copy

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

## 快速开始

### 1. 初始化项目

```bash
git-sync init
```

这会创建 `.ssh` 目录和 `keys_manifest.yaml` 文件。

### 2. 生成 SSH 密钥

```bash
# 生成名为 my-key 的 SSH 密钥
git-sync key gen -n my-key

# 查看公钥（添加到 Git 托管服务）
git-sync key show my-key
```

### 3. 创建配置文件

复制示例配置并编辑：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`:

```yaml
version: "1.0"

ssh:
  key_storage: ".ssh"
  default_key_type: "ed25519"

sync:
  temp_dir: "/tmp/git-sync"
  timeout: 300
  cleanup_after_sync: true

repositories:
  - name: "my-project"
    source:
      url: "git@github.com:source/project.git"
      ssh_key: "my-key"
    target:
      url: "git@gitlab.com:target/project.git"
      ssh_key: "my-key"
    enabled: true
    sync_branches: ["main", "develop"]  # 空列表表示同步所有分支
    sync_tags: true
```

### 4. 添加公钥到 Git 服务

将公钥添加到源仓库和目标仓库的 Git 托管服务（GitHub、GitLab、Gitea 等）。

### 5. 执行同步

```bash
# 试运行（预览操作）
git-sync sync --dry-run

# 实际同步
git-sync sync

# 同步指定仓库
git-sync sync -r my-project
```

## CLI 命令

### 全局选项

```
--version                       显示版本号
-c, --config PATH               指定配置文件路径
-v, --verbose                   启用详细输出
--log-level [DEBUG|INFO|WARNING|ERROR]  日志级别
```

### 命令列表

#### `git-sync init`

初始化 git-sync 项目，创建必要的目录和文件。

#### `git-sync key`

SSH 密钥管理命令。

```bash
# 生成密钥
git-sync key gen -n <名称> [--type ed25519|rsa]

# 列出所有密钥
git-sync key list

# 显示公钥
git-sync key show <名称>

# 删除密钥
git-sync key delete <名称>
```

#### `git-sync repo`

仓库管理命令。

```bash
# 列出配置的仓库
git-sync repo list
```

#### `git-sync sync`

同步仓库。

```bash
# 同步所有启用的仓库
git-sync sync

# 同步指定仓库
git-sync sync -r <名称>

# 试运行模式
git-sync sync --dry-run
```

## 配置说明

### SSH 配置

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `key_storage` | string | `.ssh` | SSH 密钥存储目录 |
| `default_key_type` | string | `ed25519` | 默认密钥类型 (ed25519/rsa) |

### 同步配置

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `temp_dir` | string | `/tmp/git-sync` | 临时工作目录 |
| `timeout` | int | `300` | 操作超时时间（秒） |
| `cleanup_after_sync` | bool | `true` | 同步后清理临时文件 |

### 仓库配置

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 仓库名称（唯一标识） |
| `source.url` | string | 是 | 源仓库 URL |
| `source.ssh_key` | string | 是 | 源仓库使用的 SSH 密钥名 |
| `target.url` | string | 是 | 目标仓库 URL |
| `target.ssh_key` | string | 是 | 目标仓库使用的 SSH 密钥名 |
| `enabled` | bool | 否 | 是否启用同步（默认 true） |
| `sync_branches` | list | 否 | 要同步的分支列表，空列表表示所有分支 |
| `sync_tags` | bool | 否 | 是否同步标签（默认 false） |

## 安全特性

### 快进检查

工具在推送前会检查目标分支是否可以快进合并。如果源分支和目标分支历史出现分叉，该分支会被跳过，避免意外覆盖。

### 不支持强制推送

为了安全起见，工具不支持强制推送（force push）。如果需要强制更新，请手动操作。

## 示例场景

### 场景 1：GitHub 到 GitLab 镜像

```yaml
repositories:
  - name: "mirror-project"
    source:
      url: "git@github.com:myorg/project.git"
      ssh_key: "github-key"
    target:
      url: "git@gitlab.com:myorg/project.git"
      ssh_key: "gitlab-key"
    enabled: true
    sync_branches: ["main"]
    sync_tags: true
```

### 场景 2：多仓库批量同步

```yaml
repositories:
  - name: "frontend"
    source:
      url: "git@github.com:company/frontend.git"
      ssh_key: "company-key"
    target:
      url: "git@gitlab.com:company/frontend.git"
      ssh_key: "company-key"
    enabled: true

  - name: "backend"
    source:
      url: "git@github.com:company/backend.git"
      ssh_key: "company-key"
    target:
      url: "git@gitlab.com:company/backend.git"
      ssh_key: "company-key"
    enabled: true
```

### 场景 3：自建 Gitea 同步

```yaml
repositories:
  - name: "internal-sync"
    source:
      url: "ssh://git@gitea.example.com:2222/team/project.git"
      ssh_key: "gitea-key"
    target:
      url: "ssh://git@gitea-backup.example.com:2222/team/project.git"
      ssh_key: "gitea-key"
    enabled: true
    sync_branches: []
    sync_tags: true
```

## 故障排除

### SSH 认证失败

1. 确认公钥已正确添加到 Git 托管服务
2. 检查密钥权限：`chmod 600 .ssh/<密钥名称>`
3. 手动测试连接：`ssh -i .ssh/<密钥名称> -T git@<主机>`

### 主机密钥验证失败

```bash
# 扫描并添加主机密钥
ssh-keyscan <主机> >> ~/.ssh/known_hosts
```

### 分支被跳过

如果分支因"历史分叉"被跳过，说明目标仓库的该分支有源仓库没有的提交。你需要决定是否要手动处理这个冲突。

## 许可证

MIT License
