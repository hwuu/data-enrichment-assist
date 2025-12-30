# GaussDB Ops Viewer

GaussDB 数据库运维工单浏览器，用于查看和筛选运维知识库中的问题单。

## 功能

- 两栏布局：左侧工单列表 + 右侧详情面板
- 按问题类型、负责人、得分范围筛选
- URL Hash 定位，支持分享链接直达具体工单
- 深色主题详情页，展示问题描述、根因、分析过程、解决方案

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 开发模式
python app.py

# 生产模式
uvicorn app:app --host 0.0.0.0 --port 3011 --workers 4
```

访问 http://127.0.0.1:3011

## API

| 端点 | 说明 |
|------|------|
| `GET /` | 主页面 |
| `GET /api/tickets` | 获取所有工单 |
| `GET /api/tickets/{id}` | 获取单个工单 |
| `GET /docs` | Swagger API 文档 |

## 数据库

SQLite 数据库 `gaussdb_ops.db`，包含两张表：

- `ticket_classification_2512` - 工单分类信息
- `operations_kb` - 运维知识库详情

生成测试数据：

```bash
python generate_mock_data.py
```
