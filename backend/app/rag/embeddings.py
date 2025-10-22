"""
Embedding generation using sentence-transformers
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
from app.config import settings
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Handles text embedding generation"""
    
    def __init__(self):
        self.model = None
        self.model_name = settings.embedding_model
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded successfully. Dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text string
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * settings.embedding_dimension
        
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()


@lru_cache()
def get_embedding_generator() -> EmbeddingGenerator:
    """Cached embedding generator instance"""
    return EmbeddingGenerator()


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters
        
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if overlap is None:
        overlap = settings.chunk_overlap
    
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for delimiter in ['. ', '.\n', '! ', '?\n']:
                last_delim = text[start:end].rfind(delimiter)
                if last_delim != -1:
                    end = start + last_delim + len(delimiter)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap if end < len(text) else len(text)
    
    return chunks


def prepare_job_chunks(job_data: dict) -> List[dict]:
    """
    Prepare job posting data into chunks with metadata
    
    Args:
        job_data: Dictionary containing job posting information
        
    Returns:
        List of chunks with metadata
    """
    # Combine relevant fields for embedding
    full_text = f"""
    Job Title: {job_data.get('title', '')}
    Company: {job_data.get('company', '')}
    Location: {job_data.get('location', '')}
    
    Description:
    {job_data.get('description', '')}
    
    Requirements:
    {job_data.get('requirements', '')}
    """.strip()
    
    # Create chunks
    text_chunks = chunk_text(full_text)
    
    # Prepare chunks with metadata
    prepared_chunks = []
    for idx, chunk in enumerate(text_chunks):
        chunk_data = {
            'text': chunk,
            'index': idx,
            'metadata': {
                'job_id': job_data.get('job_id'),
                'title': job_data.get('title'),
                'company': job_data.get('company'),
                'location': job_data.get('location'),
                'source_url': job_data.get('source_url'),
                'posted_date': job_data.get('posted_date'),
                'skills': job_data.get('skills', [])
            }
        }
        prepared_chunks.append(chunk_data)
    
    return prepared_chunks