# 部署指南

## 本地开发部署

### 1. 环境准备
```bash
# 克隆或下载项目到本地
cd adk_to_dify

# 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
# ADK_HOST=http://your-adk-backend:8000
# ADK_APP_NAME=your_agent_name
# PORT=8080
```

### 3. 启动服务
```bash
# 方式一：使用启动脚本
python main.py

# 方式二：使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 4. 验证部署
```bash
# 健康检查
curl http://localhost:8080/v1/health

# 运行测试脚本
python test_server.py
```

## Docker 容器部署

### 1. 构建镜像
```bash
docker build -t adk-middleware:latest .
```

### 2. 运行容器
```bash
# 单独运行
docker run -d \
  --name adk-middleware \
  -p 8080:8080 \
  -e ADK_HOST=http://your-adk-backend:8000 \
  -e ADK_APP_NAME=your_agent_name \
  adk-middleware:latest

# 使用 docker-compose
docker-compose up -d
```

### 3. 验证容器
```bash
# 查看日志
docker logs adk-middleware

# 健康检查
curl http://localhost:8080/v1/health
```

## 生产环境部署

### 1. 反向代理配置 (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /v1/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For streaming support
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

### 2. 系统服务配置 (Systemd)
```ini
[Unit]
Description=ADK Middleware Service
After=network.target

[Service]
Type=exec
User=adk
Group=adk
WorkingDirectory=/opt/adk-middleware
Environment=PATH=/opt/adk-middleware/.venv/bin
ExecStart=/opt/adk-middleware/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 3. 环境变量配置
```bash
# /etc/environment 或 .env 文件
ADK_HOST=https://your-adk-backend.internal
ADK_APP_NAME=production_agent
PORT=8080
LOG_LEVEL=WARNING
MAX_FILE_SIZE_MB=50
DOWNLOAD_TIMEOUT=60

# API Key 配置
REQUIRE_API_KEY=true                    # 生产环境建议启用
API_KEYS=sk-prod-key-1,sk-prod-key-2   # 多个 API Key 用逗号分隔
DEFAULT_API_KEY=sk-adk-middleware-key   # 默认 Key
```

## 监控和日志

### 1. 日志配置
```python
# 在生产环境中配置日志
LOG_LEVEL=WARNING  # 减少日志输出

# 使用结构化日志
import structlog
logger = structlog.get_logger()
```

### 2. 健康检查
```bash
# Kubernetes 健康检查配置
livenessProbe:
  httpGet:
    path: /v1/health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /v1/health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 3. 指标监控
```bash
# 可以集成 Prometheus 监控
# 添加指标端点到应用中
```

## 故障排除

### 常见问题

1. **连接 ADK 失败**
   - 检查 ADK_HOST 配置是否正确
   - 确认网络连通性
   - 查看防火墙设置

2. **文件下载超时**
   - 调整 DOWNLOAD_TIMEOUT 环境变量
   - 检查网络带宽
   - 验证文件 URL 是否可访问

3. **内存使用过高**
   - 调整 MAX_FILE_SIZE_MB 限制
   - 监控并发请求数
   - 考虑添加速率限制

4. **流式响应中断**
   - 检查客户端是否支持 SSE
   - 确认代理服务器配置
   - 验证网络稳定性

### 日志分析
```bash
# 查看错误日志
docker logs adk-middleware | grep ERROR

# 监控实时日志
docker logs -f adk-middleware

# 查看特定时间段的日志
journalctl -u adk-middleware --since "2024-01-01" --until "2024-01-02"
```

## 性能优化

### 1. 并发处理
```python
# 在 uvicorn 启动时增加 worker 数量
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

### 2. 缓存配置
```python
# 可以添加 Redis 缓存来缓存下载的文件
# 或使用 HTTP 缓存头
```

### 3. 资源限制
```yaml
# Kubernetes 资源限制
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## 安全配置

### 1. HTTPS 配置
```bash
# 使用 SSL/TLS 证书
# 在 Nginx 或负载均衡器中配置 HTTPS
```

### 2. 访问控制
```python
# 可以添加 API 密钥验证
# 或使用 JWT 认证
```

### 3. 网络安全
```bash
# 配置防火墙规则
# 限制访问来源
# 使用 VPN 或内网访问
```