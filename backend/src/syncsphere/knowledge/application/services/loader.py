import httpx
import re
import logging
from typing import Dict, Any

logger = logging.getLogger("syncsphere.knowledge.application.services.loader")

class DocumentNormalizer:
    """Standardizes parsed text, normalizing unicode and cleaning markup tags."""
    
    @staticmethod
    def normalize(text: str) -> str:
        # Strip simple HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Normalize whitespace characters
        text = re.sub(r"\s+", " ", text)
        return text.strip()


class DocumentParser:
    """Converts raw input data configurations (HTML, text, markdown) into clear strings."""
    
    @staticmethod
    def parse(raw_data: str, mime_type: str = "text/plain") -> str:
        # Simple plain text or markdown parsing
        normalized_data = raw_data
        if mime_type == "text/html":
            # Strip tags and normalize structure
            normalized_data = DocumentNormalizer.normalize(raw_data)
        return normalized_data


class DocumentLoader:
    """Loads raw document payloads from files, URLs, or plain configuration payloads."""
    
    @staticmethod
    async def load(source_config: Dict[str, Any]) -> str:
        """Loads target string from config configurations."""
        if "text" in source_config:
            return source_config["text"]
            
        elif "url" in source_config:
            url = source_config["url"]
            logger.info("Fetching remote URL resource: %s", url)
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url, timeout=10.0)
                    if resp.status_code == 200:
                        return resp.text
                    else:
                        raise ValueError(f"HTTP GET returned status code {resp.status_code}")
            except Exception as e:
                logger.error("Failed to load URL resource: %s", e)
                raise ValueError(f"Failed to fetch content from URL: {url}. Error: {str(e)}")
                
        elif "file_path" in source_config:
            file_path = source_config["file_path"]
            logger.info("Loading local file resource: %s", file_path)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Failed to read local file: {file_path}. Error: {str(e)}")
                
        else:
            raise ValueError("Unsupported document source configuration keys.")
