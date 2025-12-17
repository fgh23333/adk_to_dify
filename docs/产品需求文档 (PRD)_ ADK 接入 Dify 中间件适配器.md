# **产品需求文档 (PRD): ADK 接入 Dify 中间件适配器**

| 文档版本 | 日期 | 状态 | 修改描述 |
| :---- | :---- | :---- | :---- |
| v1.4 | 2025-10-27 | 正式版 | 修复文档截断问题，完整定义多模态支持与部署规范 |

## **1\. 项目背景与目标**

### **1.1 背景**

业务团队使用 **Google Agent Development Kit (ADK)** 开发了具备复杂逻辑的智能体（Agent），这些 Agent 运行在独立的后端服务中，支持长时记忆和多模态输入（文本、图片、视频、文件）。为了利用 **Dify** 平台完善的前端聊天界面、提示词编排和应用发布能力，我们需要将 ADK Agent 接入 Dify。

### **1.2 核心痛点**

1. **协议不兼容**：Dify 调用外部模型主要支持 OpenAI API 标准格式（/v1/chat/completions），而 ADK 使用自定义的 REST 接口（/run 和 /run\_sse）。  
2. **流式格式差异**：ADK 的流式输出（SSE）数据结构与 OpenAI 的 data: \[DONE\] 格式不同，Dify 无法直接解析。  
3. **会话机制差异**：Dify 每次请求发送完整历史记录（Stateless LLM 模式），而 ADK 是有状态的（Stateful），自行维护 Session 历史。直接透传会导致 ADK 重复处理历史消息。  
4. **多模态传输差异**：Dify 使用 OpenAI 格式传输图片（通常为 URL），对于视频和文件通常以链接形式嵌入文本，而 ADK 需要统一的 inlineData（Base64）格式进行多模态理解。

### **1.3 项目目标**

开发一个 **Python 中间件（Middleware Proxy）**，部署在 ADK 服务前端。它对外伪装成一个标准的 OpenAI 兼容模型服务，对内负责协议转换、多模态资源（图片/视频/文件）的下载转码和会话映射，实现 Dify 对 ADK 的无感调用。

## **2\. 系统架构设计**

### **2.1 逻辑拓扑图**

graph LR  
    User\[终端用户\] \--\> Dify\[Dify 平台\]  
      
    subgraph "中间件适配层 (Proxy)"  
    Dify \-- "1. OpenAI API 请求 (含附件URL)" \--\> Middleware\[Python Middleware\]  
    Middleware \-- "2. 解析 UserID & 截取最新消息" \--\> Middleware  
    Middleware \-- "3. 智能提取附件(图片/视频/文件) \-\> 下载 \-\> 转Base64" \--\> Middleware  
    end  
      
    subgraph "ADK 后端服务"  
    Middleware \-- "4. ADK 协议请求 (/run\_sse)" \--\> ADK\[ADK API Server\]  
    ADK \-- "5. ADK SSE 事件流" \--\> Middleware  
    end  
      
    Middleware \-- "6. 转换流格式 (OpenAI Chunk)" \--\> Dify  
    Dify \-- "7. 打字机效果渲染" \--\> User

### **2.2 核心处理流程**

1. **请求接收**：拦截 Dify 发出的符合 OpenAI 规范的 HTTP 请求。  
2. **会话绑定**：提取 Dify 请求体中的 user 字段，将其映射为 ADK 的 sessionId，确保上下文一致性。  
3. **多模态预处理（核心）**：  
   * **图片**：识别 OpenAI 消息格式中的 image\_url 字段。  
   * **视频/文件**：扫描消息文本中的 URL 链接（Dify 上传文件后通常会生成链接放入 Prompt）。  
   * **处理**：中间件发起异步请求下载这些 URL 的二进制数据，识别 MIME Type（如 video/mp4, application/pdf），转码为 Base64，并封装入 ADK 的 inlineData。  
4. **历史清洗**：丢弃 Dify 传来的 messages 历史列表，仅提取最后一条用户消息发送给 ADK（因为 ADK 自带记忆）。  
5. **流式转发**：调用 ADK /run\_sse，实时监听响应，将 ADK 的 JSON Event 转换为 OpenAI 的 Delta Content 格式并推送给 Dify。

## **3\. 功能需求说明 (Functional Requirements)**

### **3.1 接口协议转换 (P0)**

* **输入端 (面向 Dify)**：  
  * 必须实现 POST /v1/chat/completions 接口。  
  * 必须实现 GET /v1/models 接口（用于 Dify 模型列表校验）。  
  * 支持标准参数：messages, model, stream, user。  
* **输出端 (面向 ADK)**：  
  * 调用 ADK 的 POST /run\_sse (流式) 和 POST /run (非流式)。  
  * 构造符合 ADK RunRequest 结构的 Payload，包含 appName, userId, sessionId, newMessage 等。

### **3.2 流式响应支持 (Streaming) (P0)**

* **需求描述**：支持“打字机”式输出。  
* **实现逻辑**：  
  * 当请求参数 stream=True 时，中间件需与 ADK 建立长连接。  
  * 解析 ADK 返回的每一行 SSE 数据（data: {...}）。  
  * 提取 content.parts\[\].text 字段。  
  * 包装为 OpenAI 格式：data: {"choices": \[{"delta": {"content": "..."}}\]}。  
  * 流结束时发送 data: \[DONE\]。

### **3.3 深度多模态支持 (图片/文件/视频) (P0)**

* **需求描述**：ADK 需要接收 Base64 编码的多模态数据，而 Dify 传递的是 URL 或 文本链接。中间件需要承担“下载器+转码器”的角色。  
* **支持格式**：  
  * **图片**: .png, .jpg, .jpeg, .webp  
  * **文档**: .pdf, .txt  
  * **视频**: .mp4, .mov, .avi  
* **解析策略**：  
  1. **OpenAI Vision 格式解析**：  
     * 遍历 messages\[-1\].content 列表。  
     * 若 type 为 image\_url，提取 URL 下载并转 Base64。  
  2. **文本链接解析 (针对视频/文件)**：  
     * 若 Dify 将视频/文件作为 URL 拼接到 text 字段中（例如 请分析这个视频: https://.../video.mp4）。  
     * 中间件需正则提取 HTTP/HTTPS 链接。  
     * 尝试 HEAD 请求获取 Content-Type，若为支持的 MIME Type（如 video/mp4），则下载并转 Base64 放入 inlineData。  
     * **注意**：下载完成后，可选在发送给 ADK 的文本中移除该 URL，以免 LLM 混淆。  
* **ADK 封装结构**：  
  "newMessage": {  
      "role": "user",  
      "parts": \[  
          { "text": "用户的问题文本..." },  
          { "inlineData": { "mimeType": "image/jpeg", "data": "BASE64..." } },  
          { "inlineData": { "mimeType": "video/mp4", "data": "BASE64..." } }  
      \]  
  }

### **3.4 会话状态保持 (Session Management) (P0)**

* **需求描述**：用户在 Dify 上的连续对话，ADK 必须能记住上下文。  
* **实现逻辑**：  
  * Dify 的 user 字段代表最终用户 ID。  
  * 中间件需生成固定的 Session ID 规则，例如：SessionId \= "session\_" \+ Dify\_User\_Id。  
  * 每次调用 ADK 时传入此 sessionId，ADK 框架会自动加载对应的内存（Memory）。  
  * **关键点**：中间件**不要**把 Dify 传过来的 messages 列表（历史记录）全部发给 ADK，只发最新的一条 newMessage。

## **4\. 接口定义 (API Specification)**

### **4.1 对外接口：Chat Completions**

**Endpoint:** POST /v1/chat/completions

**Request Body (OpenAI 格式 \- 多模态示例):**

{  
  "model": "adk-agent",  
  "user": "dify-user-123",  
  "stream": true,  
  "messages": \[  
    {  
      "role": "user",  
      "content": \[  
        { "type": "text", "text": "分析这张图和这个视频文件" },  
        {   
          "type": "image\_url",   
          "image\_url": { "url": "\[https://dify.domain/files/image.png\](https://dify.domain/files/image.png)" }   
        }  
        // Dify 可能没有标准的 video\_url 字段，通常作为文本链接发送  
        // 或者用户直接在聊天框粘贴了视频链接  
      \]  
    }  
  \]  
}

### **4.2 对内接口：ADK Run SSE**

**Endpoint:** POST {ADK\_HOST}/run\_sse

**Request Body (ADK 格式):**

{  
  "appName": "my\_agent", // 可从 OpenAI request model 字段映射，或使用默认值  
  "userId": "dify-user-123",  
  "sessionId": "session\_dify-user-123",  
  "streaming": true,  
  "newMessage": {  
    "role": "user",  
    "parts": \[  
      { "text": "分析这张图和这个视频文件" },  
      { "inlineData": { "mimeType": "image/png", "data": "iVBORw0KGgo..." } },  
      { "inlineData": { "mimeType": "video/mp4", "data": "AAAAIGZ0eXB..." } }   
    \]  
  }  
}

## **5\. 异常处理与性能指标**

* **资源限制**：  
  * **文件大小限制**：建议限制单个附件大小（如 20MB），防止中间件内存溢出或 ADK 请求过大。若超过，返回 400 错误提示用户。  
  * **并发控制**：中间件需基于 asyncio 实现，避免下载大文件时阻塞其他请求。  
* **超时策略**：  
  * **下载超时**：15-30秒（视频文件可能较大）。  
  * **推理超时**：ADK 响应超时设为 120秒。  
* **错误映射**：  
  * 下载失败 \-\> 返回 400 Bad Request (无法获取附件)。  
  * ADK 连接失败 \-\> 返回 502 Bad Gateway。  
  * ADK 内部错误 \-\> 返回 500 Internal Server Error。

## **6\. 部署建议与环境配置**

为了保证服务的稳定运行，中间件应按照以下规范部署：

### **6.1 网络拓扑要求**

* **内网互通**：中间件应部署在与 ADK 服务相同的 VPC 或内网环境中，以保证低延迟调用 /run\_sse 接口。  
* **外网访问**：中间件容器/服务器需要具备**出网权限** (Outbound Internet **Access)**。  
  * **原因**：Dify 发送的图片或文件通常是公网 URL（例如存储在 AWS S3 或 OSS 上的链接），中间件需要访问这些 URL 来下载文件并转换为 Base64。

### **6.2 容器化部署 (Docker)**

建议将中间件打包为 Docker 镜像，保持环境一致性。

**Dockerfile 示例参考：**

FROM python:3.10-slim  
WORKDIR /app  
COPY requirements.txt .  
RUN pip install \--no-cache-dir \-r requirements.txt  
COPY . .  
CMD \["uvicorn", "proxy\_server:app", "--host", "0.0.0.0", "--port", "8081"\]

### **6.3 环境变量配置 (Environment Variables)**

中间件应支持以下环境变量，以便在不同环境（开发/生产）中灵活配置：

| 变量名 | 必填 | 默认值 | 说明 |
| :---- | :---- | :---- | :---- |
| ADK\_HOST | 是 | http://localhost:8000 | 后端 ADK 服务的地址。 |
| ADK\_APP\_NAME | 否 | default\_agent | 如果 Dify 请求中 model 字段为空时的默认 Agent 名称。 |
| PORT | 否 | 8081 | 中间件监听的端口。 |
| LOG\_LEVEL | 否 | INFO | 日志级别 (DEBUG, INFO, ERROR)。 |
| MAX\_FILE\_SIZE\_MB | 否 | 20 | 允许下载并转发的最大文件大小（MB）。 |
| DOWNLOAD\_TIMEOUT | 否 | 30 | 附件下载的超时时间（秒）。 |

### **6.4 验收标准 (Acceptance Criteria)**

1. **基础对话**：Dify 发送文本，收到流畅的打字机回复。  
2. **图片测试**：Dify 上传 PNG/JPG 图片，ADK 能准确描述图片内容。  
3. **记忆测试**：Dify 刷新页面后继续对话，ADK 能联系上下文（Session 正常工作）。  
4. **异常测试**：上传超过 20MB 的视频，中间件应立即返回错误提示，而不是让 Dify 无响应。
