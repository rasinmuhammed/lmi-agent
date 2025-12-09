"""
Local embedding generation using sentence-transformers
"""
import logging
from typing import List, Dict
from functools import lru_cache
import os

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class LocalEmbeddingGenerator:
    """Generate embeddings using local SentenceTransformers"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        try:
            logger.info(f"🔄 Loading local embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"✅ Model loaded. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            return [0.0] * self.dimension
        
        # encode returns numpy array, convert to list
        return self.model.encode(text).tolist()

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not texts:
            return []
            
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        return self.dimension

@lru_cache()
def get_embedding_generator() -> LocalEmbeddingGenerator:
    """Return cached generator instance"""
    return LocalEmbeddingGenerator()

# ============================================================
# Text Chunking for RAG
# ============================================================

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks"""
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            for punct in ['. ', '! ', '? ', '\n\n']:
                last_punct = text.rfind(punct, start, end)
                if last_punct > start + chunk_size // 2:
                    end = last_punct + len(punct)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    
    return chunks

def prepare_job_chunks(job_data: Dict) -> List[Dict]:
    """Prepare job posting data for embedding"""
    from app.config import settings

    full_text = f"Job Title: {job_data.get('title', '')}\nCompany: {job_data.get('company', '')}\nLocation: {job_data.get('location', '')}\n\nDescription:\n{job_data.get('description', '')}\n\nRequirements:\n{job_data.get('requirements', '')}\n\nSkills: {', '.join(job_data.get('skills', []))}".strip()

    text_chunks = chunk_text(full_text, chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)

    chunks = []
    for idx, chunk in enumerate(text_chunks):
        chunk_obj = {
            'text': chunk,
            'index': idx,
            'metadata': {
                'title': job_data.get('title'),
                'company': job_data.get('company'),
                'location': job_data.get('location'),
                'source_url': job_data.get('source_url'),
                'posted_date': str(job_data.get('posted_date', '')),
                'skills': job_data.get('skills', []),
            }
        }
        chunks.append(chunk_obj)

    return chunks