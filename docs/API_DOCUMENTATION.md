# ADK Web 后端接口文档

## 项目概述

ADK Web 是一个基于 Angular 的前端应用，用于与 ADK (Agent Development Kit) 后端进行交互。该项目通过 HTTP 请求和 WebSocket 连接与后端 API 进行通信。

## 配置管理

### 运行时配置

项目使用运行时配置系统来动态设置后端地址：

- **配置文件位置**: `src/assets/config/runtime-config.json`
- **配置结构**:
```json
{
  "backendUrl": "",
  "logo": {
    "url": "",
    "alt": "",
    "width": "",
    "height": ""
  }
}
```

### 配置设置方式

1. **开发环境**: 通过 npm 脚本设置
   ```bash
   npm run serve --backend=http://127.0.0.1:8000
   ```

2. **配置加载流程**:
   - `main.ts` 中通过 `fetch('./assets/config/runtime-config.json')` 加载配置
   - 配置存储在全局变量 `window['runtimeConfig']` 中
   - 通过 `URLUtil.getApiServerBaseUrl()` 获取后端 URL

## API 接口详细说明

### 基础 URL 结构

所有 API 请求的基础 URL 通过 `URLUtil.getApiServerBaseUrl()` 获取，格式为：
```
{backendUrl}/api/endpoint
```

### 1. Agent 服务 (AgentService)

#### 1.1 运行 Agent (SSE 流式响应)
- **端点**: `POST /run_sse`
- **描述**: 启动 Agent 并通过 Server-Sent Events 返回流式响应
- **请求体**: `AgentRunRequest`
- **响应**: `Observable<LlmResponse>` (SSE 流)

#### 1.2 列出应用
- **端点**: `GET /list-apps?relative_path=./`
- **描述**: 获取可用的应用列表
- **响应**: `string[]`

#### 1.3 保存 Agent 构建配置
- **端点**: `POST /builder/save`
- **描述**: 保存 Agent 的构建配置
- **请求体**: 任意 JSON 对象
- **响应**: `Observable<boolean>`

#### 1.4 保存临时 Agent 构建配置
- **端点**: `POST /builder/save?tmp=true`
- **描述**: 保存临时的 Agent 构建配置
- **请求体**: 任意 JSON 对象
- **响应**: `Observable<boolean>`

#### 1.5 获取 Agent 构建配置
- **端点**: `GET /builder/app/{agentName}?ts={timestamp}`
- **描述**: 获取指定 Agent 的构建配置
- **响应**: 文本内容

#### 1.6 获取临时 Agent 构建配置
- **端点**: `GET /builder/app/{agentName}?ts={timestamp}&tmp=true`
- **描述**: 获取指定 Agent 的临时构建配置
- **响应**: 文本内容

#### 1.7 获取子 Agent 构建配置
- **端点**: `GET /builder/app/{appName}?ts={timestamp}&file_path={relativePath}&tmp=true`
- **描述**: 获取子 Agent 的构建配置
- **响应**: 文本内容

#### 1.8 取消 Agent 变更
- **端点**: `POST /builder/app/{appName}/cancel`
- **描述**: 取消指定 Agent 的变更
- **响应**: `Observable<boolean>`

### 2. 会话服务 (SessionService)

#### 2.1 创建会话
- **端点**: `POST /apps/{appName}/users/{userId}/sessions`
- **描述**: 为指定用户和应用创建新会话
- **响应**: `Session` 对象

#### 2.2 列出会话
- **端点**: `GET /apps/{appName}/users/{userId}/sessions`
- **描述**: 获取指定用户的所有会话
- **响应**: `ListResponse<Session>`

#### 2.3 删除会话
- **端点**: `DELETE /apps/{appName}/users/{userId}/sessions/{sessionId}`
- **描述**: 删除指定会话
- **响应**: 删除结果

#### 2.4 获取会话详情
- **端点**: `GET /apps/{appName}/users/{userId}/sessions/{sessionId}`
- **描述**: 获取指定会话的详细信息
- **响应**: `Session` 对象

#### 2.5 导入会话
- **端点**: `POST /apps/{appName}/users/{userId}/sessions`
- **描述**: 导入包含事件的会话数据
- **请求体**: 
  ```json
  {
    "appName": "string",
    "userId": "string", 
    "events": []
  }
  ```
- **响应**: `Session` 对象

### 3. 事件服务 (EventService)

#### 3.1 获取事件追踪
- **端点**: `GET /debug/trace/{eventId}`
- **描述**: 获取指定事件的追踪数据
- **响应**: 追踪数据对象

#### 3.2 获取会话追踪
- **端点**: `GET /debug/trace/session/{sessionId}`
- **描述**: 获取指定会话的追踪数据
- **响应**: 追踪数据对象

#### 3.3 获取事件详情
- **端点**: `GET /apps/{appName}/users/{userId}/sessions/{sessionId}/events/{eventId}/graph`
- **描述**: 获取指定事件的图形数据
- **响应**: `{dotSrc?: string}`

### 4. 制品服务 (ArtifactService)

#### 4.1 获取最新制品
- **端点**: `GET /apps/{appName}/users/{userId}/sessions/{sessionId}/artifacts/{artifactName}`
- **描述**: 获取指定会话的最新制品
- **响应**: 制品数据

#### 4.2 获取指定版本制品
- **端点**: `GET /apps/{appName}/users/{userId}/sessions/{sessionId}/artifacts/{artifactName}/versions/{versionId}`
- **描述**: 获取指定版本的制品
- **响应**: 制品数据

### 5. 评估服务 (EvalService)

#### 5.1 获取评估集列表
- **端点**: `GET /apps/{appName}/eval_sets`
- **描述**: 获取指定应用的所有评估集
- **响应**: 评估集列表

#### 5.2 创建评估集
- **端点**: `POST /apps/{appName}/eval_sets/{evalSetId}`
- **描述**: 创建新的评估集
- **响应**: 创建结果

#### 5.3 列出评估用例
- **端点**: `GET /apps/{appName}/eval_sets/{evalSetId}/evals`
- **描述**: 获取指定评估集的所有评估用例
- **响应**: 评估用例列表

#### 5.4 添加会话到评估集
- **端点**: `POST /apps/{appName}/eval_sets/{evalSetId}/add_session`
- **描述**: 将当前会话添加到评估集
- **请求体**:
  ```json
  {
    "evalId": "string",
    "sessionId": "string", 
    "userId": "string"
  }
  ```

#### 5.5 运行评估
- **端点**: `POST /apps/{appName}/eval_sets/{evalSetId}/run_eval`
- **描述**: 运行指定评估集的评估
- **请求体**:
  ```json
  {
    "evalIds": ["string"],
    "evalMetrics": []
  }
  ```

#### 5.6 列出评估结果
- **端点**: `GET /apps/{appName}/eval_results`
- **描述**: 获取指定应用的所有评估结果
- **响应**: 评估结果列表

#### 5.7 获取评估结果详情
- **端点**: `GET /apps/{appName}/eval_results/{evalResultId}`
- **描述**: 获取指定评估结果的详细信息
- **响应**: 评估结果详情

#### 5.8 获取评估用例
- **端点**: `GET /apps/{appName}/eval_sets/{evalSetId}/evals/{evalCaseId}`
- **描述**: 获取指定评估用例的详细信息
- **响应**: 评估用例详情

#### 5.9 更新评估用例
- **端点**: `PUT /apps/{appName}/eval_sets/{evalSetId}/evals/{evalCaseId}`
- **描述**: 更新指定的评估用例
- **请求体**: `EvalCase` 对象

#### 5.10 删除评估用例
- **端点**: `DELETE /apps/{appName}/eval_sets/{evalSetId}/evals/{evalCaseId}`
- **描述**: 删除指定的评估用例
- **响应**: 删除结果

### 6. WebSocket 服务

#### 6.1 连接建立
- **协议**: 根据 HTTPS/HTTP 自动选择 WSS/WS
- **URL 格式**: `{protocol}://{host}/live`
- **描述**: 建立实时通信连接，支持音频和视频流

#### 6.2 消息格式
- **序列化**: JSON.stringify
- **反序列化**: 直接返回 event.data
- **消息类型**: `LiveRequest` 和各种响应类型

## 数据模型

### 核心模型

#### AgentRunRequest
Agent 运行请求的参数结构

#### LlmResponse
LLM 响应的数据结构，用于 SSE 流式响应

#### Session
会话对象，包含会话的基本信息和状态

#### Event
事件对象，记录 Agent 运行过程中的各种事件

#### Artifact
制品对象，存储 Agent 生成的各种输出

#### EvalCase
评估用例对象，包含评估的输入和预期输出

#### LiveRequest
实时请求对象，用于 WebSocket 通信

## 错误处理

### HTTP 错误处理
- 所有服务都检查 `apiServerDomain` 是否存在
- 当后端 URL 未配置时，返回空的 Observable
- 使用 Angular HttpClient 的标准错误处理机制

### WebSocket 错误处理
- 连接关闭时通过 `closeObserver` 处理
- 错误信息通过 `closeReasonSubject` 传递
- 支持自动重连机制

## 开发和部署

### 开发环境设置
1. 设置后端地址：
   ```bash
   npm run serve --backend=http://127.0.0.1:8000
   ```

2. 清理配置：
   ```bash
   npm run clean-config
   ```

### 生产环境配置
- 运行时配置文件需要在部署时正确设置 `backendUrl`
- 支持 HTTPS 环境下的 WSS 连接
- 支持自定义 Logo 配置

## 安全考虑

### 输入验证
- 使用 SafeValues 库处理 DOM 操作
- 对用户输入进行适当的验证和清理
- WebSocket 消息使用结构化的 JSON 格式

### 跨域处理
- 通过运行时配置支持不同域名的后端
- 遵循标准的 CORS 策略

## 会话生命周期流程

### 会话完整生命周期

ADK Web 中的会话遵循完整的生命周期模式，从创建到销毁涉及多个组件和 API 调用。

### 1. 会话创建阶段

#### 1.1 触发创建
- **入口**: `ChatComponent.createSession()`
- **触发场景**:
  - 用户进入聊天界面
  - 手动创建新会话
  - 会话重置时

#### 1.2 创建流程
```typescript
// ChatComponent.createSession()
1. 设置加载状态: uiStateService.setIsSessionListLoading(true)
2. 调用后端API: sessionService.createSession(userId, appName)
3. 处理响应:
   - 保存会话ID: this.sessionId = res.id
   - 保存会话状态: this.currentSessionState = res.state
   - 刷新会话列表: sessionTab.refreshSession()
   - 重载会话数据: sessionTab.reloadSession(sessionId)
4. 更新URL参数（如果启用）
```

#### 1.3 重置会话状态
```typescript
// ChatComponent.createSessionAndReset()
1. 创建新会话
2. 清空事件数据: this.eventData = new Map()
3. 清空消息列表: this.messages.set([])
4. 清空制品列表: this.artifacts = []
5. 清空用户输入: this.userInput = ''
6. 清空长运行事件: this.longRunningEvents = []
```

### 2. 会话运行阶段

#### 2.1 消息发送流程
```typescript
// ChatComponent.sendMessage()
1. 验证输入（文本和文件）
2. 添加用户消息到本地状态
3. 处理文件附件
4. 构建AgentRunRequest:
   - appName, userId, sessionId
   - newMessage: {role: 'user', parts: getUserMessageParts()}
   - streaming: this.useSse
   - stateDelta: this.updatedSessionState()
5. 调用Agent运行: agentService.runSse(req)
```

#### 2.2 流式响应处理
```typescript
// runSse响应处理
1. 接收SSE流式数据
2. 错误检查: chunkJson.error
3. 内容处理: chunkJson.content.parts
4. 错误消息处理: chunkJson.errorMessage
5. 动作处理: chunkJson.actions
   - 处理制品: processActionArtifact()
   - 处理状态变更: processActionStateDelta()
6. 更新UI: changeDetectorRef.detectChanges()
```

#### 2.3 事件和制品管理
- **事件追踪**: 通过EventService获取事件详情和图形数据
- **制品管理**: 通过ArtifactService获取会话生成的各种输出
- **状态同步**: 实时更新会话状态和UI显示

### 3. 会话管理阶段

#### 3.1 会话列表管理
```typescript
// SessionTab组件
1. 刷新会话列表:
   - sessionService.listSessions(userId, appName)
   - 支持分页: pageToken, pageSize
   - 支持过滤: filter参数
2. 会话排序: 按lastUpdateTime降序
3. 去重处理: 使用Map确保会话唯一性
```

#### 3.2 会话详情获取
```typescript
// SessionTab.getSession()
1. 设置加载状态: uiStateService.setIsSessionLoading(true)
2. 调用API: sessionService.getSession(userId, appName, sessionId)
3. 数据转换: fromApiResultToSession()
4. 发送事件: sessionSelected.emit(session)
5. 清除加载状态
```

#### 3.3 会话删除流程
```typescript
// 删除会话对话框
1. 用户确认删除
2. 调用API: sessionService.deleteSession(userId, appName, sessionId)
3. 刷新会话列表
4. 清理相关状态
```

#### 3.4 会话导入流程
```typescript
// ChatComponent.importSession()
1. 文件选择: accept="application/json"
2. 文件读取: FileReader.readAsText()
3. 格式验证:
   - 检查userId, appName, events字段
   - JSON解析验证
4. 调用导入API: sessionService.importSession()
5. 刷新会话列表
6. 显示成功提示
```

### 4. 会话生命周期时序图

```
用户操作        ChatComponent        SessionService        后端API
   |               |                    |                    |
创建会话 --------> |                    |                    |
   |               | createSession() --> |                    |
   |               |                    | POST /sessions     |
   |               | <------------------ | Session对象        |
   |               | 保存sessionId      |                    |
   |               | 刷新UI             |                    |
   |               |                    |                    |
发送消息 --------> |                    |                    |
   |               | sendMessage() ----> |                    |
   |               | runSse() ---------> | POST /run_sse      |
   |               | <------------------ | SSE流式响应        |
   |               | 处理流式数据       |                    |
   |               | 更新UI             |                    |
   |               |                    |                    |
查看列表 --------> |                    |                    |
   |               |                    | listSessions() ---> |
   |               |                    | GET /sessions      |
   |               |                    | <------------------ | 会话列表
   |               |                    | 更新会话列表       |
   |               |                    |                    |
删除会话 --------> |                    |                    |
   |               |                    | deleteSession() --> |
   |               |                    | DELETE /sessions/{id}
   |               |                    | <------------------ | 删除结果
   |               |                    | 刷新列表           |
   |               |                    |                    |
导入会话 --------> |                    |                    |
   |               | importSession() --> |                    |
   |               |                    | POST /sessions     |
   |               |                    | <------------------ | 导入结果
   |               | 刷新列表           |                    |
```

### 5. 会话状态管理

#### 5.1 状态类型
- **SessionState**: 会话的当前状态
- **Event**: 会话中的事件记录
- **Artifact**: 会话生成的制品
- **Message**: 用户和Agent的对话消息

#### 5.2 状态同步机制
- **实时同步**: 通过SSE流式更新
- **手动刷新**: 通过reloadSession()和refreshSession()
- **缓存管理**: 本地状态与后端状态的一致性

### 6. 错误处理和恢复

#### 6.1 创建失败处理
- 显示错误提示
- 重置加载状态
- 保持原有会话状态

#### 6.2 运行时错误处理
- SSE连接错误处理
- 消息发送失败重试
- 状态回滚机制

#### 6.3 网络异常处理
- 自动重连机制
- 离线状态提示
- 数据本地缓存

### 7. 性能优化

### 流式响应
- Agent 运行使用 SSE 进行流式响应
- WebSocket 支持实时音频和视频传输
- 合理的缓存策略和连接管理

### 资源管理
- 服务使用 `providedIn: 'root'` 进行单例管理
- 适当的 Observable 生命周期管理
- WebSocket 连接的正确关闭和清理

### 会话性能优化
- **分页加载**: 会话列表支持分页，避免一次性加载大量数据
- **懒加载**: 会话详情按需加载
- **状态缓存**: 本地缓存会话状态，减少API调用
- **防抖处理**: 用户输入和搜索的防抖处理
- **内存管理**: 及时清理不需要的会话数据和事件

## run_sse 详细流程分析

### 1. 请求构建流程

#### 1.1 AgentRunRequest 结构
```typescript
interface AgentRunRequest {
  appName: string;           // 应用名称
  userId: string;            // 用户ID
  sessionId: string;         // 会话ID
  newMessage: {
    role: 'user';            // 消息角色
    parts: Array<{           // 消息内容部分
      text?: string;         // 文本内容
      function_response?: {  // 函数响应
        id?: string;
        name?: string;
        response?: any;
      }
    }>;
  };
  streaming?: boolean;       // 是否启用流式响应
  stateDelta?: any;          // 状态变更
  invocationId?: string;     // 调用ID
}
```

#### 1.2 请求构建过程
```typescript
// ChatComponent.sendMessage()
1. 输入验证: 检查文本和文件
2. 添加用户消息到本地状态
3. 处理文件附件
4. 构建请求参数:
   - appName, userId, sessionId
   - newMessage: getUserMessageParts()
   - streaming: this.useSse (默认false)
   - stateDelta: updatedSessionState()
5. 清空选择文件和流式消息状态
6. 调用 agentService.runSse(req)
```

#### 1.3 消息部分构建
```typescript
// getUserMessageParts()
1. 文本部分: {text: userInput}
2. 文件部分: localFileService.createMessagePartFromFile(file)
3. 返回parts数组
```

### 2. SSE 响应处理机制

#### 2.1 SSE 连接建立
```typescript
// AgentService.runSse()
1. 发送POST请求到 /run_sse
2. 设置请求头:
   - Content-Type: application/json
   - Accept: text/event-stream
3. 获取ReadableStream reader
4. 循环读取数据块
5. 解析SSE格式数据
6. 通过Observable发送给订阅者
```

#### 2.2 SSE 数据解析
```typescript
// SSE数据格式处理
1. 数据块解码: TextDecoder('utf-8')
2. 行分割: split(/\r?\n/)
3. 过滤data行: line.startsWith('data:')
4. 移除data前缀: line.replace(/^data:\s*/, '')
5. JSON解析: JSON.parse(data)
6. 错误处理: 无效JSON等待下一块
```

#### 2.3 响应数据结构
```typescript
interface LlmResponse (AdkEvent) {
  id?: string;                    // 事件ID
  content?: {
    parts: Part[];               // 内容部分
  };
  actions?: {                    // 动作
    artifactDelta?: any;         // 制品变更
    stateDelta?: any;           // 状态变更
  };
  errorMessage?: string;         // 错误消息
  error?: string;               // 错误信息
  author?: string;              // 作者
  groundingMetadata?: any;      // 元数据
}
```

### 3. 消息显示流程

#### 3.1 响应处理主流程
```typescript
// runSse.subscribe()
next: async (chunkJson: AdkEvent) => {
  1. 错误检查: chunkJson.error -> 显示错误提示
  2. 内容处理: chunkJson.content -> processPart()
  3. 错误消息: chunkJson.errorMessage -> processErrorMessage()
  4. 动作处理: chunkJson.actions -> processActionArtifact(), processActionStateDelta()
  5. UI更新: changeDetectorRef.detectChanges()
}
error: (err) -> 错误提示
complete: () -> 完成处理
```

#### 3.2 文本部分处理
```typescript
// processPart(chunkJson, part)
1. 文本合并: combineTextParts() - 合并连续文本
2. 思考消息处理:
   - part.thought === true
   - 检查 newChunk !== latestThought
   - 创建思考消息并插入
3. 流式文本处理:
   - 首次创建: !streamingTextMessage
   - 追加内容: streamingTextMessage.text += newChunk
   - 重复检查: newChunk == streamingTextMessage.text
4. 非文本处理: storeMessage()
```

#### 3.3 消息插入机制
```typescript
// insertMessageBeforeLoadingMessage()
1. 检查最后消息是否为加载状态
2. 如果是加载消息: 在加载消息前插入
3. 如果不是: 直接追加到末尾
```

#### 3.4 消息存储机制
```typescript
// storeMessage()
1. 创建Agent图标颜色类
2. 处理长运行工具: getAsyncFunctionsFromParts()
3. OAuth认证处理
4. 制品渲染: renderArtifact()
5. 评估状态处理
6. 构建消息对象并插入
```

### 4. 重复回复问题分析

#### 4.1 可能的重复原因

##### 4.1.1 流式文本处理逻辑问题
```typescript
// 问题代码位置
if (newChunk == this.streamingTextMessage.text) {
  this.storeEvents(part, chunkJson);
  this.streamingTextMessage = null;
  return;
}
this.streamingTextMessage.text += newChunk;
```

**问题分析**:
- 当接收到与当前流式消息完全相同的内容时，会清空流式消息
- 但如果后续还有内容，可能会重新创建消息
- 可能导致消息重复显示

##### 4.1.2 思考消息重复
```typescript
// 思考消息处理
if (newChunk !== this.latestThought) {
  // 创建新的思考消息
  this.insertMessageBeforeLoadingMessage(thoughtMessage);
}
this.latestThought = newChunk;
```

**问题分析**:
- 思考消息每次内容变化都会创建新消息
- 如果思考过程有重复内容，可能导致重复显示

##### 4.1.3 事件存储重复
```typescript
// 多处调用storeEvents
this.storeEvents(part, chunkJson);
this.storeEvents(null, e);
```

**问题分析**:
- 同一个事件可能被多次存储
- 可能导致事件重复处理

##### 4.1.4 SSE数据重复
```typescript
// SSE解析逻辑
lines.forEach((line) => {
  const data = line.replace(/^data:\s*/, '');
  const llmResponse = JSON.parse(data) as LlmResponse;
  self.zone.run(() => observer.next(llmResponse));
});
```

**问题分析**:
- 如果后端发送重复的SSE数据
- 前端会重复处理相同的响应

#### 4.2 重复回复的解决方案

##### 4.2.1 添加消息去重机制
```typescript
// 建议的解决方案
private processedEventIds = new Set<string>();

private processPart(chunkJson: any, part: any) {
  // 检查事件ID是否已处理
  if (chunkJson.id && this.processedEventIds.has(chunkJson.id)) {
    return;
  }
  
  if (chunkJson.id) {
    this.processedEventIds.add(chunkJson.id);
  }
  
  // 原有处理逻辑...
}
```

##### 4.2.2 改进流式文本处理
```typescript
// 改进的流式文本处理
if (newChunk == this.streamingTextMessage.text) {
  // 避免重复处理相同内容
  return;
}

// 检查是否为追加内容
if (this.streamingTextMessage.text.endsWith(newChunk)) {
  return;
}

this.streamingTextMessage.text += newChunk;
```

##### 4.2.3 思考消息去重
```typescript
// 改进的思考消息处理
if (part.thought && newChunk !== this.latestThought) {
  // 检查是否已有相同的思考消息
  const hasSameThought = this.messages().some(msg => 
    msg.thought && msg.text.includes(newChunk)
  );
  
  if (!hasSameThought) {
    this.insertMessageBeforeLoadingMessage(thoughtMessage);
  }
}
```

##### 4.2.4 后端配合优化
```typescript
// 建议后端优化
1. 确保SSE数据不重复发送
2. 添加唯一事件ID
3. 优化文本分块逻辑
4. 避免思考内容重复
```

### 5. 调试和排查指南

#### 5.1 前端调试方法
```typescript
// 添加调试日志
console.log('Received chunk:', chunkJson);
console.log('Current streaming message:', this.streamingTextMessage);
console.log('Latest thought:', this.latestThought);
console.log('Messages count:', this.messages().length);
```

#### 5.2 网络请求检查
1. 检查Network面板中的SSE请求
2. 查看接收到的数据块内容
3. 确认是否有重复的data行
4. 检查请求参数是否正确

#### 5.3 状态检查
```typescript
// 检查关键状态
console.log('useSse:', this.useSse);
console.log('sessionId:', this.sessionId);
console.log('currentSessionState:', this.currentSessionState);
```

#### 5.4 常见问题排查
1. **重复文本**: 检查流式文本处理逻辑
2. **重复思考**: 检查思考消息去重机制
3. **重复事件**: 检查事件ID处理
4. **状态异常**: 检查会话状态管理

### 6. 最佳实践建议

#### 6.1 开发建议
1. **启用SSE**: 确保useSse设置为true
2. **状态管理**: 正确管理会话状态和消息状态
3. **错误处理**: 完善的错误处理和用户提示
4. **性能优化**: 避免频繁的UI更新

#### 6.2 测试建议
1. **单元测试**: 测试各种响应处理场景
2. **集成测试**: 测试完整的消息流程
3. **压力测试**: 测试大量消息的处理性能
4. **边界测试**: 测试异常情况的处理

#### 6.3 监控建议
1. **错误监控**: 监控SSE连接和解析错误
2. **性能监控**: 监控消息处理延迟
3. **用户体验**: 监控重复回复等用户体验问题
4. **资源使用**: 监控内存和CPU使用情况

## FastAPI 中间件处理流程详解

### 1. 架构概述

您的系统采用三层架构：
```
前端(ADK Web) → FastAPI中间层 → ADK后端
```

FastAPI中间件负责：
- 接收前端ADK格式的请求
- 转换为OpenAI格式
- 调用OpenAI兼容的API
- 将OpenAI响应转换回ADK格式
- 处理SSE流式响应

### 2. 请求处理流程

#### 2.1 接收ADK格式请求
```python
# FastAPI端点定义
@app.post("/run_sse")
async def run_agent_sse(request: AgentRunRequest):
    """
    处理来自ADK Web的SSE请求
    """
    pass
```

#### 2.2 ADK请求格式解析
```python
# ADK AgentRunRequest结构
class AgentRunRequest(BaseModel):
    appName: str
    userId: str
    sessionId: Optional[str]
    newMessage: Message
    streaming: bool = False
    stateDelta: Optional[Dict]
    invocationId: Optional[str]

class Message(BaseModel):
    role: str  # "user"
    parts: List[MessagePart]

class MessagePart(BaseModel):
    text: Optional[str]
    function_response: Optional[FunctionResponse]
```

#### 2.3 转换为OpenAI格式
```python
def convert_to_openai_format(adk_request: AgentRunRequest) -> ChatCompletionRequest:
    """
    将ADK格式转换为OpenAI ChatCompletion格式
    """
    # 提取用户消息内容
    user_content = []
    for part in adk_request.newMessage.parts:
        if part.text:
            user_content.append({"type": "text", "text": part.text})
        elif part.function_response:
            user_content.append({
                "type": "function_response",
                "function_response": part.function_response.dict()
            })
    
    # 构建OpenAI消息格式
    messages = [
        {
            "role": "user",
            "content": user_content if len(user_content) > 1 else user_content[0]["text"]
        }
    ]
    
    # 转换为OpenAI请求格式
    openai_request = ChatCompletionRequest(
        model=adk_request.appName,  # 使用appName作为model
        messages=messages,
        stream=adk_request.streaming,
        user=adk_request.userId,
        # 其他OpenAI参数...
    )
    
    return openai_request
```

### 3. OpenAI API调用

#### 3.1 同步调用处理
```python
async def call_openai_api(openai_request: ChatCompletionRequest):
    """
    调用OpenAI兼容的API
    """
    try:
        # 调用OpenAI API
        response = await openai_client.chat.completions.create(
            model=openai_request.model,
            messages=openai_request.messages,
            stream=openai_request.stream,
            user=openai_request.user
        )
        return response
    except Exception as e:
        logger.error(f"OpenAI API调用失败: {e}")
        raise HTTPException(status_code=500, detail="API调用失败")
```

#### 3.2 流式响应处理
```python
async def handle_streaming_response(openai_response, adk_request: AgentRunRequest):
    """
    处理OpenAI流式响应并转换为ADK格式
    """
    async def generate_sse():
        try:
            # 生成唯一的事件ID
            event_id = str(uuid.uuid4())
            
            async for chunk in openai_response:
                # 转换OpenAI chunk到ADK格式
                adk_event = convert_openai_chunk_to_adk(chunk, event_id)
                
                # 格式化为SSE
                sse_data = f"data: {adk_event.json()}\n\n"
                yield sse_data
                
        except Exception as e:
            # 错误处理
            error_event = {
                "id": event_id,
                "error": f"流式响应处理错误: {str(e)}",
                "errorMessage": "处理响应时发生错误"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )
```

### 4. 响应格式转换

#### 4.1 OpenAI Chunk到ADK Event转换
```python
def convert_openai_chunk_to_adk(chunk, event_id: str) -> Dict:
    """
    将OpenAI流式响应chunk转换为ADK事件格式
    """
    if chunk.choices[0].delta.content is not None:
        # 文本内容响应
        return {
            "id": event_id,
            "content": {
                "parts": [
                    {
                        "text": chunk.choices[0].delta.content,
                        "thought": False
                    }
                ]
            },
            "author": "agent",
            "timestamp": time.time()
        }
    
    elif chunk.choices[0].delta.role is not None:
        # 角色信息（通常在流开始时）
        return {
            "id": event_id,
            "author": chunk.choices[0].delta.role,
            "timestamp": time.time()
        }
    
    # 其他类型的响应...
    return {"id": event_id, "timestamp": time.time()}

def convert_openai_response_to_adk(response, event_id: str) -> Dict:
    """
    将OpenAI完整响应转换为ADK事件格式
    """
    choice = response.choices[0]
    
    return {
        "id": event_id,
        "content": {
            "parts": [
                {
                    "text": choice.message.content,
                    "thought": False
                }
            ]
        },
        "author": "agent",
        "timestamp": time.time(),
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        } if response.usage else None
    }
```

### 5. 重复回复问题分析

#### 5.1 在FastAPI中间件中可能的原因

##### 5.1.1 事件ID重复使用
```python
# 问题代码示例
event_id = str(uuid.uuid4())  # 在函数开始时生成一次

async for chunk in openai_response:
    adk_event = convert_openai_chunk_to_adk(chunk, event_id)  # 同一个event_id
    yield f"data: {adk_event.json()}\n\n"
```

**问题**: 所有chunk使用同一个event_id，前端可能认为是重复事件

**解决方案**:
```python
async def generate_sse():
    chunk_index = 0
    base_event_id = str(uuid.uuid4())
    
    async for chunk in openai_response:
        # 为每个chunk生成唯一ID
        event_id = f"{base_event_id}_{chunk_index}"
        adk_event = convert_openai_chunk_to_adk(chunk, event_id)
        yield f"data: {adk_event.json()}\n\n"
        chunk_index += 1
```

##### 5.1.2 OpenAI响应重复处理
```python
# 可能的问题：OpenAI返回重复内容
async for chunk in openai_response:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        
        # 检查是否为重复内容
        if hasattr(handle_streaming_response, 'last_content'):
            if content == handle_streaming_response.last_content:
                continue  # 跳过重复内容
        
        handle_streaming_response.last_content = content
        # 处理内容...
```

##### 5.1.3 SSE格式错误
```python
# 错误的SSE格式
yield f"data: {adk_event.json()}\n"  # 缺少额外的换行符

# 正确的SSE格式
yield f"data: {adk_event.json()}\n\n"  # 需要两个换行符
```

#### 5.2 针对您情况的解决方案

##### 5.2.1 完整的FastAPI处理函数
```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import uuid
import time
import asyncio
from openai import AsyncOpenAI

app = FastAPI()

class MessagePart(BaseModel):
    text: Optional[str] = None
    function_response: Optional[Dict[str, Any]] = None

class Message(BaseModel):
    role: str
    parts: List[MessagePart]

class AgentRunRequest(BaseModel):
    appName: str
    userId: str
    sessionId: Optional[str] = None
    newMessage: Message
    streaming: bool = False
    stateDelta: Optional[Dict[str, Any]] = None
    invocationId: Optional[str] = None

# OpenAI客户端
openai_client = AsyncOpenAI(
    base_url="your-openai-compatible-endpoint",
    api_key="your-api-key"
)

@app.post("/run_sse")
async def run_agent_sse(request: AgentRunRequest):
    """
    处理ADK Web的run_sse请求
    """
    try:
        # 转换为OpenAI格式
        openai_request = convert_to_openai_format(request)
        
        if request.streaming:
            # 流式响应处理
            return await handle_streaming_response(openai_request, request)
        else:
            # 同步响应处理
            return await handle_sync_response(openai_request, request)
            
    except Exception as e:
        logger.error(f"处理请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_streaming_response(openai_request, adk_request: AgentRunRequest):
    """
    处理流式响应
    """
    async def generate_sse():
        base_event_id = str(uuid.uuid4())
        chunk_index = 0
        last_content = ""
        
        try:
            # 调用OpenAI API
            response = await openai_client.chat.completions.create(
                model=openai_request.model,
                messages=openai_request.messages,
                stream=True,
                user=openai_request.user
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    
                    # 去重检查
                    if content == last_content:
                        continue
                    
                    last_content = content
                    
                    # 生成唯一事件ID
                    event_id = f"{base_event_id}_{chunk_index}"
                    
                    # 转换为ADK格式
                    adk_event = {
                        "id": event_id,
                        "content": {
                            "parts": [
                                {
                                    "text": content,
                                    "thought": False
                                }
                            ]
                        },
                        "author": "agent",
                        "timestamp": time.time()
                    }
                    
                    # 发送SSE数据
                    yield f"data: {json.dumps(adk_event)}\n\n"
                    chunk_index += 1
            
            # 发送完成事件
            complete_event = {
                "id": f"{base_event_id}_complete",
                "actions": {
                    "stateDelta": adk_request.stateDelta
                },
                "timestamp": time.time()
            }
            yield f"data: {json.dumps(complete_event)}\n\n"
            
        except Exception as e:
            # 错误处理
            error_event = {
                "id": f"{base_event_id}_error",
                "error": str(e),
                "errorMessage": f"处理流式响应时发生错误: {str(e)}",
                "timestamp": time.time()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )

async def handle_sync_response(openai_request, adk_request: AgentRunRequest):
    """
    处理同步响应
    """
    try:
        response = await openai_client.chat.completions.create(
            model=openai_request.model,
            messages=openai_request.messages,
            stream=False,
            user=openai_request.user
        )
        
        event_id = str(uuid.uuid4())
        adk_event = convert_openai_response_to_adk(response, event_id)
        
        return adk_event
        
    except Exception as e:
        logger.error(f"同步响应处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def convert_to_openai_format(adk_request: AgentRunRequest):
    """
    将ADK请求转换为OpenAI格式
    """
    # 提取消息内容
    content_parts = []
    for part in adk_request.newMessage.parts:
        if part.text:
            content_parts.append(part.text)
    
    # 构建OpenAI消息
    user_message = {
        "role": "user",
        "content": " ".join(content_parts) if content_parts else ""
    }
    
    # 构建完整消息历史（如果有会话历史）
    messages = [user_message]
    
    # 这里可以添加会话历史的处理逻辑
    # if adk_request.sessionId:
    #     messages.extend(get_session_history(adk_request.sessionId))
    
    class OpenAIRequest:
        def __init__(self):
            self.model = adk_request.appName
            self.messages = messages
            self.stream = adk_request.streaming
            self.user = adk_request.userId
            self.temperature = 0.7
            self.max_tokens = 2000
    
    return OpenAIRequest()
```

### 6. 调试和监控

#### 6.1 添加详细日志
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/run_sse")
async def run_agent_sse(request: AgentRunRequest):
    logger.info(f"收到请求: {request.json()}")
    
    try:
        # 记录转换后的OpenAI请求
        openai_request = convert_to_openai_format(request)
        logger.info(f"转换后的OpenAI请求: model={openai_request.model}, messages={openai_request.messages}")
        
        # 处理响应...
        
    except Exception as e:
        logger.error(f"处理失败: {e}", exc_info=True)
        raise
```

#### 6.2 性能监控
```python
import time
from contextlib import asynccontextmanager

@asynccontextmanager
async def monitor_performance(operation_name: str):
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        logger.info(f"{operation_name} 耗时: {end_time - start_time:.2f}秒")

@app.post("/run_sse")
async def run_agent_sse(request: AgentRunRequest):
    async with monitor_performance("run_sse"):
        # 处理逻辑...
        pass
```

### 7. 针对重复回复的最终解决方案

#### 7.1 在FastAPI中的完整去重逻辑
```python
async def generate_sse_with_deduplication(response, adk_request: AgentRunRequest):
    """
    带去重功能的SSE生成器
    """
    base_event_id = str(uuid.uuid4())
    chunk_index = 0
    content_buffer = ""
    sent_contents = set()  # 已发送内容的集合
    
    async for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            new_content = chunk.choices[0].delta.content
            
            # 累积内容
            content_buffer += new_content
            
            # 检查是否已发送过相同内容
            if content_buffer in sent_contents:
                logger.warning(f"检测到重复内容，跳过: {content_buffer[:50]}...")
                continue
            
            # 标记为已发送
            sent_contents.add(content_buffer)
            
            # 生成事件ID
            event_id = f"{base_event_id}_{chunk_index}"
            
            # 创建ADK事件
            adk_event = {
                "id": event_id,
                "content": {
                    "parts": [
                        {
                            "text": content_buffer,
                            "thought": False
                        }
                    ]
                },
                "author": "agent",
                "timestamp": time.time()
            }
            
            yield f"data: {json.dumps(adk_event)}\n\n"
            chunk_index += 1
            
            # 重置缓冲区（根据需要）
            if len(content_buffer) > 1000:  # 避免缓冲区过大
                content_buffer = ""
```
这个完整的处理流程应该能帮助您解决重复回复的问题，并提供一个稳定可靠的FastAPI中间件服务。