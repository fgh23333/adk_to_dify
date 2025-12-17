import re
import base64
import mimetypes
from typing import List, Optional, Tuple
import httpx
from app.config import settings
from app.models import ContentPart, ADKPart, ADKInlineData
import logging

logger = logging.getLogger(__name__)


class MultimodalProcessor:
    def __init__(self):
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.timeout = settings.download_timeout
        
    async def process_content(self, content_parts: List[ContentPart]) -> Tuple[str, List[ADKPart]]:
        """
        Process content parts, extracting text and handling multimodal content.
        Returns tuple of (combined_text, adk_parts)
        """
        text_parts = []
        adk_parts = []
        
        logger.info(f"Starting multimodal processing for {len(content_parts)} content parts")
        
        for i, part in enumerate(content_parts):
            logger.info(f"Processing content part {i}: type={part.type}")
            
            if part.type == "text" and part.text:
                logger.info(f"Found text part: {part.text[:100]}...")
                text_parts.append(part.text)
                # Extract URLs from text for video/file processing
                urls = self._extract_urls_from_text(part.text)
                logger.info(f"Found {len(urls)} URLs in text: {urls}")
                for url in urls:
                    try:
                        logger.info(f"Attempting to download URL: {url}")
                        inline_data = await self._download_and_convert_url(url)
                        if inline_data:
                            logger.info(f"Successfully downloaded and converted URL: {inline_data.mimeType}")
                            adk_parts.append(ADKPart(inlineData=inline_data))
                        else:
                            logger.warning(f"Failed to download URL: {url} - no data returned")
                    except Exception as e:
                        logger.error(f"Failed to process URL {url}: {e}")
                        
            elif part.type == "image_url" and part.image_url:
                logger.info(f"Found image_url part: {part.image_url.url[:100]}...")
                try:
                    logger.info(f"Attempting to download image URL: {part.image_url.url}")
                    inline_data = await self._download_and_convert_url(part.image_url.url)
                    if inline_data:
                        logger.info(f"Successfully downloaded and converted image: {inline_data.mimeType}, data length: {len(inline_data.data)}")
                        adk_parts.append(ADKPart(inlineData=inline_data))
                    else:
                        logger.warning(f"Failed to download image URL: {part.image_url.url} - no data returned")
                except Exception as e:
                    logger.error(f"Failed to process image URL {part.image_url.url}: {e}")
            else:
                logger.warning(f"Unsupported content part type: {part.type}")
        
        # Combine all text parts
        combined_text = " ".join(text_parts)
        
        # Add text part if we have combined text
        if combined_text.strip():
            adk_parts.insert(0, ADKPart(text=combined_text))
            
        return combined_text, adk_parts
    
    def _extract_urls_from_text(self, text: str) -> List[str]:
        """Extract HTTP/HTTPS URLs from text using regex."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return urls
    
    async def _download_and_convert_url(self, url: str) -> Optional[ADKInlineData]:
        """
        Download file from URL and convert to base64 inline data.
        Returns None if download fails or file is too large.
        """
        logger.info(f"Starting download of URL: {url}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, get content type and file size with HEAD request
                logger.info(f"Sending HEAD request to: {url}")
                head_response = await client.head(url)
                logger.info(f"HEAD response status: {head_response.status_code}")
                
                content_type = head_response.headers.get('content-type', '')
                content_length = head_response.headers.get('content-length')
                
                logger.info(f"Content-Type: {content_type}, Content-Length: {content_length}")
                
                # Check file size
                if content_length and int(content_length) > self.max_file_size:
                    logger.warning(f"File too large: {content_length} bytes > {self.max_file_size} bytes")
                    return None
                
                # Download the file
                logger.info(f"Starting GET request to download file")
                response = await client.get(url)
                logger.info(f"GET response status: {response.status_code}")
                response.raise_for_status()
                
                # Check actual file size
                actual_size = len(response.content)
                logger.info(f"Downloaded {actual_size} bytes")
                
                if actual_size > self.max_file_size:
                    logger.warning(f"Downloaded file too large: {actual_size} bytes")
                    return None
                
                # Determine MIME type
                if not content_type:
                    content_type, _ = mimetypes.guess_type(url)
                    if not content_type:
                        # Default to binary if we can't determine the type
                        content_type = 'application/octet-stream'
                
                logger.info(f"Final MIME type: {content_type}")
                
                # Convert to base64
                base64_data = base64.b64encode(response.content).decode('utf-8')
                logger.info(f"Converted to base64, length: {len(base64_data)}")
                
                return ADKInlineData(
                    mimeType=content_type,
                    data=base64_data
                )
                
        except httpx.TimeoutException:
            logger.error(f"Timeout downloading URL: {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading URL {url}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error downloading URL {url}: {e}")
            return None