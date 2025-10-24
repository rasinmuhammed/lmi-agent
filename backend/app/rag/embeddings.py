"""
Optimized Embedding generation using sentence-transformers
"""
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from app.config import settings
from functools import lru_cache
import logging
import torch
import math

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Handles text embedding generation with optimized memory and speed"""

    def __init__(self, batch_size: int = None):
        self.model = None
        self.model_name = settings.embedding_model
        self.device = "cpu"
        self.batch_size = batch_size
        self._load_model()

    def _load_model(self):
        """Load the embedding model with device auto-detection and logging"""
        try:
            # Auto-detect device
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"

            # Adjust batch size for device
            if self.batch_size is None:
                self.batch_size = 16 if self.device in ["cuda", "mps"] else 2

            logger.info(f"Loading embedding model: {self.model_name} on device={self.device}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Model loaded successfully. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            return [0.0] * settings.embedding_dimension

        return self.generate_embeddings_batch([text])[0]

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = None) -> List[List[float]]:
        """Generate embeddings in batches for large input lists to avoid OOM"""
        if not texts:
            return []

        batch_size = batch_size or self.batch_size
        all_embeddings = []

        # Process in small batches
        num_batches = math.ceil(len(texts) / batch_size)
        for i in range(num_batches):
            batch_texts = texts[i * batch_size : (i + 1) * batch_size]
            try:
                batch_embeddings = self.model.encode(
                    batch_texts,
                    batch_size=len(batch_texts),
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                all_embeddings.extend(batch_embeddings.tolist())
            except Exception as e:
                logger.warning(f"Batch encoding failed: {e}. Falling back to individual encoding.")
                # Fallback: encode individually
                for text in batch_texts:
                    embedding = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
                    all_embeddings.append(embedding[0].tolist())

        return all_embeddings

    def get_dimension(self) -> int:
        """Return embedding dimension"""
        return self.model.get_sentence_embedding_dimension()


@lru_cache()
def get_embedding_generator() -> EmbeddingGenerator:
    """Return cached embedding generator instance"""
    return EmbeddingGenerator()


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if overlap is None:
        overlap = settings.chunk_overlap
    
    if not text:
        return
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            for delimiter in ['. ', '.\n', '! ', '?\n']:
                last_delim = text[start:end].rfind(delimiter)
                if last_delim != -1:
                    end = start + last_delim + len(delimiter)
                    break
        chunk = text[start:end].strip()
        if chunk:
            yield chunk
        start = end - overlap if end < len(text) else len(text)

def prepare_job_chunks(job_data: dict) -> List[dict]:
    """Prepare job posting data into text chunks with metadata"""
    full_text = f"""
Job Title: {job_data.get('title', '')}
Company: {job_data.get('company', '')}
Location: {job_data.get('location', '')}

Description:
{job_data.get('description', '')}

Requirements:
{job_data.get('requirements', '')}
""".strip()

    text_chunks = chunk_text(full_text)
    prepared_chunks = []

    for idx, chunk in enumerate(text_chunks):
        prepared_chunks.append({
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
        })

    return prepared_chunks
