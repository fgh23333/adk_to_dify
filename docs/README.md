# ADK 接入 Dify 中间件适配器

一个 Python 中间件服务，用于将 Google Agent Development Kit (ADK) 的自定义 REST/SSE 接口转换为 OpenAI 兼容的 API 格式，以便接入 Dify 平台。

## 功能特性

- ✅ **协议转换**: 将 OpenAI 格式的 `/v1/chat/completions` 请求转换为 ADK 的 `/run` 或 `/run_sse` 请求
- ✅ **多模态支持**: 自动下载并转换图片、视频、文件为 Base64 格式
- ✅ **会话管理**: 基于 Dify 的 `user` 字段维护 ADK 的 `sessionId`
- ✅ **流式响应**: 支持 SSE 流式输出，实现打字机效果
- ✅ **历史清洗**: 智能丢弃历史记录，仅发送最新消息给 ADK
- ✅ **错误处理**: 完整的异常处理和日志记录

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置 ADK 后端地址
ADK_HOST=http://localhost:8000
ADK_APP_NAME=your_agent_name
PORT=8080

# API Key 配置（可选）
REQUIRE_API_KEY=false                    # 是否启用 API Key 验证
API_KEYS=sk-adk-middleware-key           # 允许的 API Key 列表（逗号分隔）
DEFAULT_API_KEY=sk-adk-middleware-key    # 默认 API Key
```

### 3. 启动服务

```bash
# 方式一：使用启动脚本
python main.py

# 方式二：直接使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 4. 验证服务

```bash
# 健康检查（无需 API Key）
curl http://localhost:8080/v1/health

# 获取模型列表（如果启用了 API Key 验证）
curl -X GET http://localhost:8080/v1/models \
  -H "Authorization: Bearer sk-adk-middleware-key"

# 测试对话接口（如果启用了 API Key 验证）
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-adk-middleware-key" \
  -d '{
    "model": "default_agent",
    "messages": [{"role": "user", "content": "Hello!"}],
    "user": "test_user"
  }'
```

## API Key 认证

本中间件支持 OpenAI 兼容的 API Key 认证机制。

### 启用 API Key 验证

在 `.env` 文件中设置：
```bash
REQUIRE_API_KEY=true
API_KEYS=sk-your-key-1,sk-your-key-2,sk-adk-middleware-key
```

### 使用 API Key

在请求头中添加 Authorization：
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-adk-middleware-key" \
  -d '{...}'
```

### 在 Dify 中配置

1. 在 Dify 的模型配置中，选择"自定义模型"
2. 模型基础 URL: `http://your-middleware-host:8080/v1`
3. API Key: `sk-adk-middleware-key`（或您配置的任意有效 Key）
4. 模型名称: `default_agent`（或您在 ADK_APP_NAME 中配置的名称）

### 默认 API Key

如果未启用验证或需要快速测试，可以使用默认 API Key：
```
sk-adk-middleware-key
```

## API 接口

### POST /v1/chat/completions

创建对话补全，支持流式和非流式响应。

**请求头:**
- `Content-Type: application/json`
- `Authorization: Bearer YOUR_API_KEY` (如果启用了验证)

**请求参数:**
- `model`: ADK Agent 名称
- `messages`: 对话消息列表
- `stream`: 是否流式响应 (默认: false)
- `user`: 用户ID (用于会话管理)
- `temperature`: 采样温度 (可选)

**多模态支持:**
- 图片: `{"type": "image_url", "image_url": {"url": "..."}}`
- 文件/视频: 自动识别文本中的 URL 链接并下载转换

### GET /v1/models

获取可用的 ADK Agent 列表。

### GET /v1/health

健康检查接口。

## 环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| ADK_HOST | 是 | http://localhost:8000 | ADK 后端服务地址 |
| ADK_APP_NAME | 否 | default_agent | 默认 Agent 名称 |
| PORT | 否 | 8080 | 中间件监听端口 |
| LOG_LEVEL | 否 | INFO | 日志级别 |
| MAX_FILE_SIZE_MB | 否 | 20 | 最大文件大小限制 |
| DOWNLOAD_TIMEOUT | 否 | 30 | 文件下载超时时间 |
| REQUIRE_API_KEY | 否 | false | 是否启用 API Key 验证 |
| API_KEYS | 否 | sk-adk-middleware-key | 允许的 API Key 列表（逗号分隔） |
| DEFAULT_API_KEY | 否 | sk-adk-middleware-key | 默认 API Key |

## 项目结构

```
adk_to_dify/
├── app/
│   ├── __init__.py          # 包初始化
│   ├── main.py              # FastAPI 主应用
│   ├── config.py            # 配置管理
│   ├── models.py            # 数据模型
│   ├── adk_client.py        # ADK 协议转换
│   └── multimodal.py        # 多模态处理
├── main.py                  # 启动入口
├── requirements.txt         # 依赖列表
├── .env.example            # 环境变量模板
└── README.md               # 项目文档
```

## 核心逻辑

### 会话映射
- Dify `user` 字段 → ADK `sessionId` (格式: `session_{user}`)
- 确保同一用户的连续对话在 ADK 中保持上下文

### 历史清洗
- Dify 发送完整 `messages` 列表 (Stateless)
- 中间件仅提取最后一条用户消息发送给 ADK (Stateful)
- ADK 自行维护对话历史

### 多模态处理
1. 解析 OpenAI 消息格式中的 `image_url` 字段
2. 扫描文本内容中的 HTTP/HTTPS 链接
3. 异步下载资源并识别 MIME 类型
4. 转换为 Base64 并封装为 ADK `inlineData` 格式

### 流式转换
- 监听 ADK SSE 事件流
- 提取 `content.parts[].text` 字段
- 实时转换为 OpenAI Chunk 格式
- 结束时发送 `data: [DONE]`

## 错误处理

| 状态码 | 说明 | 场景 |
|--------|------|------|
| 400 | Bad Request | 无效输入、文件下载失败、文件超限 |
| 500 | Internal Server Error | 中间件内部错误 |
| 502 | Bad Gateway | ADK 连接失败 |

## 部署建议

### Docker 部署

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 网络要求
- 中间件需要与 ADK 服务内网互通
- 中间件需要出网权限以下载 Dify 传递的文件 URL

---

## 📚 文档目录说明

本 `docs/` 目录包含项目的所有文档文件：

### 核心文档
- **README.md** - 项目主要说明文档（本文件）
- **API_DOCUMENTATION.md** - 详细的API文档和接口说明
- **产品需求文档 (PRD)_ ADK 接入 Dify 中间件适配器.md** - 产品需求文档

### 设计文档
- **api_design_document.md** - API设计文档
- **api-server.md** - API服务器相关文档

### 部署文档
- **DEPLOYMENT.md** - 部署指南和说明

### 接口规范
- **openapi.json** - OpenAPI接口规范文件

### 📖 阅读建议

如果您是第一次接触此项目，建议按以下顺序阅读：

1. **[README.md](README.md)** - 了解项目基本信息和快速开始
2. **[产品需求文档](产品需求文档%20(PRD)_%20ADK%20接入%20Dify%20中间件适配器.md)** - 理解项目需求和背景
3. **[API文档](API_DOCUMENTATION.md)** - 学习详细的API使用方法和接口说明
4. **[部署文档](DEPLOYMENT.md)** - 了解部署方法和配置说明

### 🔗 快速导航

- **快速开始** → 参考上方的"快速开始"部分
- **API参考** → [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **部署指南** → [DEPLOYMENT.md](DEPLOYMENT.md)
- **需求文档** → [产品需求文档](产品需求文档%20(PRD)_%20ADK%20接入%20Dify%20中间件适配器.md)

## 许可证

MIT License