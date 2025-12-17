import logging
import base64
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, Any

from app.config import settings
from app.models import (
    ChatCompletionRequest, ChatCompletionResponse, ListModelsResponse,
    HealthResponse, ErrorResponse
)
from app.adk_client import ADKClient
from app.auth import verify_api_key_dependency

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize ADK client
adk_client = ADKClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("ADK Middleware starting up...")
    yield
    # Shutdown
    logger.info("ADK Middleware shutting down...")


# Create FastAPI app
app = FastAPI(
    title="ADK Middleware API",
    description="Middleware API for exposing Google ADK agents as OpenAI-compatible Chat Completion endpoints",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"message": "Internal server error", "type": "internal_error"}}
    )


@app.post("/v1/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    api_key_valid: bool = Depends(verify_api_key_dependency)
):
    """Create a chat completion (streaming or non-streaming)."""
    try:
        logger.info(f"=== CHAT COMPLETION REQUEST START ===")
        logger.info(f"Model: {request.model}, User: {request.user}, Stream: {request.stream}")
        
        # Log the complete request for debugging
        logger.info(f"Complete request: {request.model_dump()}")
        
        # Log detailed message information
        logger.info(f"Request has {len(request.messages)} messages")
        for i, msg in enumerate(request.messages):
            logger.info(f"Message {i}: role={msg.role}, content_type={type(msg.content).__name__}")
            if isinstance(msg.content, str):
                logger.info(f"  Content (string): '{msg.content}'")
            else:
                logger.info(f"  Content (array): {len(msg.content)} parts")
                for j, part in enumerate(msg.content):
                    logger.info(f"    Part {j}: type={part.type}")
                    if part.type == "text" and part.text:
                        logger.info(f"      Text: '{part.text}'")
                    elif part.type == "image_url" and part.image_url:
                        logger.info(f"      Image URL: '{part.image_url.url}'")
                    else:
                        logger.warning(f"      Unknown part content: {part}")
        
        logger.info(f"=== CHAT COMPLETION REQUEST END ===")
        
        # Validate request
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                adk_client.create_chat_completion_stream(request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )
        else:
            # Return non-streaming response
            response = await adk_client.create_chat_completion(request)
            logger.info(f"Successfully generated response for user: {request.user}")
            return response
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPStatusError as e:
        # Handle error without reading response content that might be closed
        logger.error(f"ADK HTTP error: {e.response.status_code} - {e.response.reason_phrase}")
        if e.response.status_code >= 500:
            raise HTTPException(status_code=502, detail="ADK service unavailable")
        else:
            raise HTTPException(status_code=400, detail="Bad request to ADK service")
    except Exception as e:
        logger.error(f"Error creating chat completion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/models")
async def list_models(
    api_key_valid: bool = Depends(verify_api_key_dependency)
) -> ListModelsResponse:
    """List available models (ADK agents)."""
    try:
        logger.info("Received models list request")
        response = await adk_client.list_models()
        return response
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    api_key: HTTPAuthorizationCredentials = Depends(verify_api_key_dependency)
) -> Dict[str, Any]:
    """
    上传文件并转换为Base64格式供ADK使用
    """
    try:
        from app.multimodal import MultimodalProcessor
        processor = MultimodalProcessor()
        
        # 读取文件内容
        file_content = await file.read()
        
        # 验证和处理文件
        is_valid, error_msg, detected_mime = processor.validate_file(
            file_content, file.filename, file.content_type
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 转换为Base64
        inline_data = processor.process_base64_file(
            base64.b64encode(file_content).decode('utf-8'),
            file.filename,
            detected_mime
        )
        
        if not inline_data:
            raise HTTPException(status_code=500, detail="文件处理失败")
        
        return {
            "success": True,
            "filename": file.filename,
            "mime_type": inline_data.mimeType,
            "base64_data": inline_data.data,
            "size": len(file_content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ADK Middleware API is running", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower()
    )