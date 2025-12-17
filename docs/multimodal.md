## 多模态输入实现详解

### 1. 多模态架构概述

ADK Web 支持多种输入模态，包括：
- **文本输入**: 传统的文本消息
- **文件上传**: 图片、文档等文件
- **图片处理**: 图片显示、预览和传输

### 2. 文件上传机制

#### 2.1 文件选择和存储
```typescript
// ChatComponent中的文件管理
selectedFiles: {file: File; url: string}[] = [];

onFileSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files) {
    for (let i = 0; i < input.files.length; i++) {
      const file = input.files[i];
      // 创建本地预览URL
      const url = this.safeValuesService.createObjectUrl(file);
      this.selectedFiles.push({file, url});
    }
  }
  input.value = ''; // 清空input，允许重复选择同一文件
}

removeFile(index: number) {
  // 释放URL资源
  URL.revokeObjectURL(this.selectedFiles[index].url);
  this.selectedFiles.splice(index, 1);
}
```

#### 2.2 文件转换为消息部分
```typescript
// LocalFileService实现
async createMessagePartFromFile(file: File): Promise<any> {
  return {
    inlineData: {
      displayName: file.name,
      data: await this.readFileAsBytes(file),
      mimeType: file.type,
    },
  };
}

private readFileAsBytes(file: File): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e: any) => {
      // 提取Base64数据部分
      const base64Data = e.target.result.split(',')[1];
      resolve(base64Data);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file); // 读取为Base64
  });
}
```

#### 2.3 多模态消息构建
```typescript
// ChatComponent.getUserMessageParts()
async getUserMessageParts() {
  let parts: any = [];

  // 添加文本部分
  if (!!this.userInput.trim()) {
    parts.push({text: `${this.userInput}`});
  }

  // 添加文件部分
  if (this.selectedFiles.length > 0) {
    for (const file of this.selectedFiles) {
      parts.push(
        await this.localFileService.createMessagePartFromFile(file.file)
      );
    }
  }
  return parts;
}
```

### 3. 图片处理流程

#### 3.1 图片显示和预览
```typescript
// 消息中的图片处理
if (part.inlineData) {
  const base64Data = this.formatBase64Data(
    part.inlineData.data, part.inlineData.mimeType
  );
  message.inlineData = {
    displayName: part.inlineData.displayName,
    data: base64Data,
    mimeType: part.inlineData.mimeType,
  };
}

// Base64数据格式化
private formatBase64Data(data: string, mimeType: string) {
  const fixedBase64Data = fixBase64String(data);
  return `data:${mimeType};base64,${fixedBase64Data}`;
}
```

#### 3.2 图片渲染和查看
```typescript
// 图片点击查看大图
viewImage(imageData: string, mimeType: string) {
  const dialogRef = this.dialog.open(ViewImageDialogComponent, {
    data: {imageData, mimeType},
    width: '80%',
    height: '80%',
  });
}
```

#### 3.3 制品图片处理
```typescript
// 处理Agent生成的图片制品
private renderArtifact(artifactId: string, versionId: string) {
  // 添加占位消息
  let message = {
    role: 'bot',
    inlineData: {
      data: '',
      mimeType: 'image/png',
    },
  };
  this.insertMessageBeforeLoadingMessage(message);

  // 获取图片数据
  this.artifactService.getArtifactVersion(
    this.userId, this.appName, this.sessionId, 
    artifactId, versionId
  ).subscribe((res) => {
    const {mimeType, data} = res.inlineData ?? {};
    if (mimeType && data) {
      const inlineData = {
        data: this.formatBase64Data(data, mimeType),
        mimeType,
      };
      // 更新占位消息
      this.updateMessageWithImageData(inlineData);
    }
  });
}
```

### 4. 文件类型处理

#### 4.1 支持的文件类型
```typescript
// 支持的文件类型配置
const SUPPORTED_FILE_TYPES = {
  images: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  documents: [
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  ],
  archives: [
    'application/zip',
    'application/x-rar-compressed'
  ]
};

// 文件大小限制（字节）
const FILE_SIZE_LIMITS = {
  image: 10 * 1024 * 1024,      // 10MB
  document: 20 * 1024 * 1024,   // 20MB
  archive: 50 * 1024 * 1024     // 50MB
};
```

#### 4.2 文件验证
```typescript
// 文件验证函数
private validateFile(file: File): {valid: boolean, error?: string} {
  // 检查文件类型
  const allSupportedTypes = [
    ...SUPPORTED_FILE_TYPES.images,
    ...SUPPORTED_FILE_TYPES.documents,
    ...SUPPORTED_FILE_TYPES.archives
  ];
  
  if (!allSupportedTypes.includes(file.type)) {
    return {
      valid: false,
      error: `不支持的文件类型: ${file.type}`
    };
  }
  
  // 检查文件大小
  let sizeLimit = FILE_SIZE_LIMITS.document; // 默认限制
  if (SUPPORTED_FILE_TYPES.images.includes(file.type)) {
    sizeLimit = FILE_SIZE_LIMITS.image;
  } else if (SUPPORTED_FILE_TYPES.archives.includes(file.type)) {
    sizeLimit = FILE_SIZE_LIMITS.archive;
  }
  
  if (file.size > sizeLimit) {
    return {
      valid: false,
      error: `文件大小超过限制 (${(sizeLimit / 1024 / 1024).toFixed(1)}MB)`
    };
  }
  
  return {valid: true};
}

// 增强的文件选择处理
onFileSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  if (!input.files) return;
  
  const validFiles: {file: File; url: string}[] = [];
  const errors: string[] = [];
  
  for (let i = 0; i < input.files.length; i++) {
    const file = input.files[i];
    const validation = this.validateFile(file);
    
    if (validation.valid) {
      const url = this.safeValuesService.createObjectUrl(file);
      validFiles.push({file, url});
    } else {
      errors.push(`${file.name}: ${validation.error}`);
    }
  }
  
  // 显示错误信息
  if (errors.length > 0) {
    this.openSnackBar(errors.join('\n'), 'OK');
  }
  
  // 添加有效文件
  this.selectedFiles.push(...validFiles);
  input.value = '';
}
```

### 5. FastAPI后端文件上传支持

#### 5.1 基础文件上传处理
```python
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import base64
import io
import os
from pathlib import Path

app = FastAPI(title="ADK File Upload API")

# 配置上传目录
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 支持的文件类型
SUPPORTED_TYPES = {
    "images": ["image/jpeg", "image/png", "image/gif", "image/webp"],
    "documents": [
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
}

# 文件大小限制（字节）
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

@app.post("/upload_files")
async def upload_files(
    files: List[UploadFile] = File(...),
    user_id: str = Form(...),
    session_id: str = Form(...)
):
    """
    处理文件上传
    """
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            # 验证文件类型
            all_supported = []
            for types in SUPPORTED_TYPES.values():
                all_supported.extend(types)
            
            if file.content_type not in all_supported:
                errors.append(f"{file.filename}: 不支持的文件类型")
                continue
            
            # 验证文件大小
            file_content = await file.read()
            if len(file_content) > MAX_FILE_SIZE:
                errors.append(f"{file.filename}: 文件大小超过限制")
                continue
            
            # 保存文件
            file_path = UPLOAD_DIR / f"{user_id}_{session_id}_{file.filename}"
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            # 转换为Base64用于传输
            base64_content = base64.b64encode(file_content).decode('utf-8')
            
            file_info = {
                "name": file.filename,
                "type": file.content_type,
                "size": len(file_content),
                "data": base64_content,
                "path": str(file_path)
            }
            
            uploaded_files.append(file_info)
            
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return {
        "success": len(uploaded_files) > 0,
        "files": uploaded_files,
        "errors": errors,
        "user_id": user_id,
        "session_id": session_id
    }

@app.post("/run_sse_with_files")
async def run_agent_sse_with_files(
    request: AgentRunRequest,
    files: Optional[List[UploadFile]] = File(None)
):
    """
    处理带文件的Agent运行请求
    """
    try:
        # 处理上传的文件
        file_parts = []
        if files:
            for file in files:
                content = await file.read()
                base64_content = base64.b64encode(content).decode('utf-8')
                
                file_part = {
                    "inlineData": {
                        "displayName": file.filename,
                        "data": base64_content,
                        "mimeType": file.content_type
                    }
                }
                file_parts.append(file_part)
        
        # 合并到消息部分中
        if hasattr(request.newMessage, 'parts'):
            request.newMessage.parts.extend(file_parts)
        else:
            request.newMessage.parts = file_parts
        
        # 转换为OpenAI格式并处理
        openai_request = convert_multimodal_to_openai(request)
        
        if request.streaming:
            return await handle_streaming_response(openai_request, request)
        else:
            return await handle_sync_response(openai_request, request)
            
    except Exception as e:
        logger.error(f"处理多模态请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 5.2 多模态格式转换
```python
def convert_multimodal_to_openai(adk_request: AgentRunRequest):
    """
    将ADK多模态请求转换为OpenAI格式
    """
    messages = []
    content_parts = []
    
    # 处理所有消息部分
    for part in adk_request.newMessage.parts:
        if part.text:
            # 文本内容
            content_parts.append({
                "type": "text",
                "text": part.text
            })
        elif part.inlineData:
            # 文件内容
            if part.inlineData.mimeType.startswith('image/'):
                # 图片文件 - 使用OpenAI Vision API格式
                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{part.inlineData.mimeType};base64,{part.inlineData.data}"
                    }
                })
            else:
                # 其他文件类型 - 作为文本描述处理
                content_parts.append({
                    "type": "text",
                    "text": f"附件: {part.inlineData.displayName} ({part.inlineData.mimeType})"
                })
    
    # 构建消息
    if content_parts:
        if len(content_parts) == 1 and content_parts[0]["type"] == "text":
            # 纯文本消息
            messages.append({
                "role": "user",
                "content": content_parts[0]["text"]
            })
        else:
            # 多模态消息
            messages.append({
                "role": "user",
                "content": content_parts
            })
    
    class OpenAIRequest:
        def __init__(self):
            self.model = adk_request.appName
            self.messages = messages
            self.stream = adk_request.streaming
            self.user = adk_request.userId
            self.max_tokens = 2000
    
    return OpenAIRequest()

@app.get("/download_file/{file_id}")
async def download_file(file_id: str):
    """
    下载已上传的文件
    """
    try:
        # 根据file_id查找文件
        file_path = None
        for file in UPLOAD_DIR.glob("*"):
            if file_id in file.name:
                file_path = file
                break
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="文件未找到")
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 6. 前端UI组件

#### 6.1 文件上传组件
```html
<!-- 文件选择按钮 -->
<input 
  type="file" 
  (change)="onFileSelect($event)"
  multiple
  accept="image/*,.pdf,.doc,.docx,.txt"
  #fileInput
>

<!-- 已选择文件的预览 -->
<div *ngFor="let file of selectedFiles; let i = index" class="file-preview">
  <img [src]="file.url" *ngIf="file.file.type.startsWith('image/')" 
       [alt]="file.file.name" class="preview-image">
  <div class="file-info">
    <span>{{ file.file.name }}</span>
    <span>{{ (file.file.size / 1024).toFixed(2) }} KB</span>
  </div>
  <button (click)="removeFile(i)" class="remove-btn">×</button>
</div>
```

#### 6.2 文件预览组件
```html
<!-- 文件预览区域 -->
<div class="file-preview-container">
  <div *ngFor="let file of selectedFiles; let i = index" class="file-preview">
    <!-- 图片预览 -->
    <img [src]="file.url" *ngIf="file.file.type.startsWith('image/')" 
         [alt]="file.file.name" class="preview-image">
    
    <!-- 文档图标 -->
    <div *ngIf="!file.file.type.startsWith('image/')" class="document-icon">
      <mat-icon>description</mat-icon>
    </div>
    
    <div class="file-info">
      <span class="file-name">{{ file.file.name }}</span>
      <span class="file-size">{{ formatFileSize(file.file.size) }}</span>
    </div>
    
    <button (click)="removeFile(i)" class="remove-btn" mat-icon-button>
      <mat-icon>close</mat-icon>
    </button>
  </div>
</div>
```

### 7. 错误处理和优化

#### 7.1 文件大小限制
```typescript
// 文件大小检查
private validateFileSize(file: File): boolean {
  const maxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > maxSize) {
    this.openSnackBar(`文件 ${file.name} 超过10MB限制`, 'OK');
    return false;
  }
  return true;
}

// 文件类型检查
private validateFileType(file: File): boolean {
  const allowedTypes = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf', 'text/plain', 
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ];
  
  if (!allowedTypes.includes(file.type)) {
    this.openSnackBar(`不支持的文件类型: ${file.type}`, 'OK');
    return false;
  }
  return true;
}
```

#### 7.2 文件处理优化
```typescript
// 文件大小格式化
formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 文件类型图标获取
getFileIcon(mimeType: string): string {
  if (mimeType.startsWith('image/')) return 'image';
  if (mimeType.includes('pdf')) return 'picture_as_pdf';
  if (mimeType.includes('word')) return 'description';
  if (mimeType.includes('excel')) return 'table_chart';
  if (mimeType.includes('text')) return 'text_snippet';
  return 'attach_file';
}

// 批量文件验证
validateFiles(files: File[]): {valid: File[], errors: string[]} {
  const valid: File[] = [];
  const errors: string[] = [];
  
  files.forEach(file => {
    const sizeValidation = this.validateFileSize(file);
    const typeValidation = this.validateFileType(file);
    
    if (sizeValidation && typeValidation) {
      valid.push(file);
    } else {
      if (!sizeValidation) {
        errors.push(`${file.name}: 文件大小超过限制`);
      }
      if (!typeValidation) {
        errors.push(`${file.name}: 不支持的文件类型`);
      }
    }
  });
  
  return { valid, errors };
}
```

### 8. 部署配置

#### 8.1 文件上传限制
```python
# FastAPI配置
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="ADK Multimodal API",
    max_request_size=50 * 1024 * 1024,  # 50MB
    max_upload_size=10 * 1024 * 1024     # 10MB per file
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 8.2 文件处理依赖
```python
# requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
openai>=1.0.0
pillow>=10.0.0   # 图像处理
python-magic>=0.4.27  # 文件类型检测
aiofiles>=23.0.0      # 异步文件操作
```

这个简化的多模态实现指南为您提供了专注于文件上传的前后端解决方案，包括文件上传、图片处理、文档处理等功能。该实现去除了实时音频和视频流处理，专注于稳定的文件传输和处理，适合大多数不需要实时功能的应用场景。您可以根据具体需求进一步扩展和调整相应的模块。