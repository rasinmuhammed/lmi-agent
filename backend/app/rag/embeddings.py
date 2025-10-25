"""
Hugging Face Inference API embeddings - bypasses local MPS issues
"""
import requests
import time
import logging
from typing import List
from functools import lru_cache
from app.config import settings

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingGenerator:
    """Generate embeddings using Hugging Face Inference API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.huggingface_api_key
        self.model_name = settings.embedding_model
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY not set in environment")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Initialized HuggingFace API embeddings: {self.model_name}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        return self.generate_embeddings_batch([text])[0]
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings in batches with retry logic"""
        if not texts:
            return []
        
        all_embeddings = []
        
        # Process in batches to respect rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                embeddings = self._call_api(batch)
                all_embeddings.extend(embeddings)
                
                # Rate limiting - be nice to free tier
                if i + batch_size < len(texts):
                    time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Batch {i}-{i+len(batch)} failed: {e}")
                # Fallback: try individual texts
                for text in batch:
                    try:
                        emb = self._call_api([text])[0]
                        all_embeddings.append(emb)
                        time.sleep(0.5)
                    except Exception as e2:
                        logger.error(f"Individual text failed: {e2}")
                        all_embeddings.append([0.0] * self.dimension)
        
        return all_embeddings
    
    def _call_api(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """Call Hugging Face API with retry logic"""
        payload = {
            "inputs": texts,
            "options": {"wait_for_model": True}
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle different response formats
                    if isinstance(result, list):
                        # If single text, result is 2D array
                        if len(texts) == 1 and isinstance(result[0], (int, float)):
                            return [result]
                        # If multiple texts, result is 3D array
                        return result
                    else:
                        raise ValueError(f"Unexpected response format: {type(result)}")
                
                elif response.status_code == 503:
                    # Model loading
                    logger.warning(f"Model loading, attempt {attempt + 1}/{max_retries}")
                    time.sleep(5 * (attempt + 1))
                    continue
                
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    raise Exception(f"API returned {response.status_code}")
            
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout, attempt {attempt + 1}/{max_retries}")
                time.sleep(2 * (attempt + 1))
                continue
            
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2 * (attempt + 1))
        
        raise Exception("Max retries exceeded")
    
    def get_dimension(self) -> int:
        """Return embedding dimension"""
        return self.dimension


@lru_cache()
def get_hf_embedding_generator() -> HuggingFaceEmbeddingGenerator:
    """Return cached HF embedding generator instance"""
    return HuggingFaceEmbeddingGenerator()


# Update config.py to use this
def get_embedding_generator():
    """
    Get appropriate embedding generator based on configuration
    
    Priority:
    1. HuggingFace API (if key available) - no memory issues
    2. Local model (fallback)
    """
    try:
        # Try HuggingFace API first
        return get_hf_embedding_generator()
    except ValueError:
        logger.warning("HuggingFace API key not found, using local model")
        # Fallback to local (will be slow/crash on M1)
        from app.rag.embeddings import get_embedding_generator as get_local
        return get_local()