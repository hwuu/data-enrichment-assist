# GaussDB Ops Viewer

GaussDB 数据库运维工单浏览器，用于查看、筛选和审核运维知识库中的问题单。

## 功能

- 两栏布局：左侧工单列表 + 右侧详情面板
- 按问题类型、负责人、得分范围、审核状态筛选
- 审核功能：通过/不通过/待定，支持填写审核意见
- 审核状态图标：✓通过 ✗不通过 ◐待定 ⚠过期 ○未审核
- 导出 Excel：支持按当前筛选和排序导出
- 外部链接：可配置跳转到原始工单系统
- URL Hash 定位，支持分享链接直达具体工单
- 支持 SQLite 和 PostgreSQL 数据库

## 快速开始

### Docker (推荐)

```bash
# 构建镜像
docker build -t gaussdb-ops-viewer .

# 运行 (SQLite)
docker run -d -p 3011:3011 \
  -v /path/to/gaussdb_ops.db:/app/gaussdb_ops.db \
  gaussdb-ops-viewer

# 运行 (PostgreSQL + 外部链接)
docker run -d -p 3011:3011 \
  -e DB_TYPE=postgresql \
  -e DB_HOST=your-db-host \
  -e DB_PORT=5432 \
  -e DB_NAME=gaussdb_ops \
  -e DB_USER=postgres \
  -e DB_PASSWORD=your-password \
  -e TICKET_URL_PATTERN="http://your-system/ticket/{processId}" \
  gaussdb-ops-viewer
```

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 生成测试数据
python generate_mock_data.py

# 启动服务
python app.py

# 启动服务 (带外部链接)
# PowerShell:
$env:TICKET_URL_PATTERN = "http://example.com/ticket/{processId}"; python app.py
# Linux/macOS:
TICKET_URL_PATTERN="http://example.com/ticket/{processId}" python app.py
```

访问 http://127.0.0.1:3011

## 配置

通过环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_TYPE` | `sqlite` | 数据库类型: `sqlite` / `postgresql` |
| `DB_PATH` | `gaussdb_ops.db` | SQLite 数据库路径 |
| `DB_HOST` | `localhost` | PostgreSQL 主机 |
| `DB_PORT` | `5432` | PostgreSQL 端口 |
| `DB_NAME` | `gaussdb_ops` | PostgreSQL 数据库名 |
| `DB_USER` | `postgres` | PostgreSQL 用户名 |
| `DB_PASSWORD` | - | PostgreSQL 密码 |
| `SERVER_HOST` | `127.0.0.1` | 服务监听地址 |
| `SERVER_PORT` | `3011` | 服务端口 |
| `WORKERS` | `4` | uvicorn worker 数量 (Docker) |
| `TICKET_URL_PATTERN` | - | 外部工单链接模板，如 `http://abc/{processId}` |

## API

| 端点 | 说明 |
|------|------|
| `GET /` | 主页面 |
| `GET /api/tickets` | 获取所有工单 |
| `GET /api/tickets/{id}` | 获取单个工单详情 |
| `GET /api/tickets/{id}/review` | 获取工单审核意见 |
| `POST /api/tickets/{id}/review` | 保存工单审核意见 |
| `GET /api/export` | 导出 Excel (支持筛选参数) |
| `GET /docs` | Swagger API 文档 |

## 审核状态

| 状态 | 图标 | 说明 |
|------|------|------|
| 通过 | ✓ 绿色 | 审核通过 |
| 不通过 | ✗ 红色 | 审核不通过 |
| 待定 | ◐ 橙色 | 待进一步确认 |
| 过期 | ⚠ 紫色 | 工单更新后审核未更新 |
| 未审核 | ○ 灰色 | 尚未审核 |

## 项目结构

```
├── app.py              # FastAPI 应用入口
├── config.py           # 配置管理
├── database.py         # 数据库抽象层
├── Dockerfile
├── generate_mock_data.py
├── requirements.txt
└── templates/
    └── index.html
```
