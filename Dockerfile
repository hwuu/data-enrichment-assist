# GaussDB Ops Viewer Docker Image
#
# 构建:
#   docker build -t gaussdb-ops-viewer .
#
# 运行:
#   docker run -d -p 3011:3011 \
#     -v /path/to/gaussdb_ops.db:/app/gaussdb_ops.db \
#     gaussdb-ops-viewer
#
# 使用 PostgreSQL:
#   docker run -d -p 3011:3011 \
#     -e DB_TYPE=postgresql \
#     -e DB_HOST=your-db-host \
#     -e DB_PORT=5432 \
#     -e DB_NAME=gaussdb_ops \
#     -e DB_USER=postgres \
#     -e DB_PASSWORD=your-password \
#     gaussdb-ops-viewer

#FROM python:3.11-slim
FROM crpi-123cnbgmjz0ihmia.cn-beijing.personal.cr.aliyuncs.com/hwuu00_mirror/python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY app.py .
COPY config.py .
COPY database.py .
COPY templates/ ./templates/

# 环境变量
ENV DB_TYPE=sqlite
ENV DB_PATH=/app/gaussdb_ops.db
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=3011
ENV WORKERS=4
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 3011

# 启动服务
CMD ["sh", "-c", "uvicorn app:app --host ${SERVER_HOST} --port ${SERVER_PORT} --workers ${WORKERS}"]
