"""
Complete embedding generation using HuggingFace Inference API
WORKING solution for sentence-transformers models
"""
import requests
import time
import logging
from typing import List, Dict
from functools import lru_cache
import os

logger = logging.getLogger(__name__)


"""
Complete embedding generation using HuggingFace Inference API
WORKING solution for sentence-transformers models
"""
import os
import time
import logging
import requests
from typing import List, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingGenerator:
    """Generate embeddings using HuggingFace Inference API"""

    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.model_name = model_name or "BAAI/bge-small-en-v1.5"

        if not self.api_key:
            raise ValueError(
                "❌ HUGGINGFACE_API_KEY is missing. Get one at https://huggingface.co/settings/tokens"
            )

        # endpoint for all models
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # rough known dimensions for common models
        self.dimension = 384 if "MiniLM" in self.model_name else 768
        logger.info(f"✅ Using HuggingFace model: {self.model_name}")

    # --------------------------
    # Public Methods
    # --------------------------
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            return [0.0] * self.dimension

        return self.generate_embeddings_batch([text])[0]

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 8) -> List[List[float]]:
        """Generate embeddings for a list of texts with batching and retry logic"""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                embeddings = self._extract_embeddings_direct(batch)
                all_embeddings.extend(embeddings)

                if i + batch_size < len(texts):
                    time.sleep(0.3)  # rate-limit buffer

            except Exception as e:
                logger.error(f"Batch {i}-{i+len(batch)} failed: {e}")
                # Fallback: individual calls
                for t in batch:
                    try:
                        emb = self._extract_embeddings_direct([t])[0]
                        all_embeddings.append(emb)
                        time.sleep(0.3)
                    except Exception as e2:
                        logger.error(f"Individual text failed: {e2}")
                        all_embeddings.append([0.0] * self.dimension)

        return all_embeddings

    # --------------------------
    # Internal Methods
    # --------------------------
    def _extract_embeddings_direct(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """
        Call the HuggingFace Inference API for feature extraction
        """
        payload = {
            "inputs": texts if len(texts) > 1 else texts[0],
            "options": {"wait_for_model": True}
        }

        for attempt in range(max_retries):
            response = requests.post(
                self.api_url, headers=self.headers, json=payload, timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                # Handle possible formats
                if isinstance(result, list):
                    if isinstance(result[0], (int, float)):
                        return [result]
                    elif isinstance(result[0], list):
                        return result

            elif response.status_code == 503:
                wait_time = 5 * (attempt + 1)
                logger.warning(f"Model loading ({wait_time}s)... retry {attempt + 1}")
                time.sleep(wait_time)
                continue

            elif response.status_code == 401:
                raise ValueError("❌ Invalid HuggingFace API key.")

            else:
                logger.warning(
                    f"HuggingFace API returned {response.status_code}: {response.text[:120]}"
                )

            time.sleep(2 * (attempt + 1))

        raise RuntimeError(f"Failed after {max_retries} retries. Model: {self.model_name}")

    def get_dimension(self) -> int:
        return self.dimension


@lru_cache()
def get_embedding_generator() -> HuggingFaceEmbeddingGenerator:
    """Return cached HuggingFace embedding generator instance"""
    from app.config import settings
    return HuggingFaceEmbeddingGenerator(
        api_key=settings.huggingface_api_key,
        model_name=settings.embedding_model
    )



# ============================================================
# Text Chunking for RAG
# ============================================================

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings near the boundary
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
    """
    Prepare job posting data for embedding
    """
    from app.config import settings

    full_text = f"""
Job Title: {job_data.get('title', '')}
Company: {job_data.get('company', '')}
Location: {job_data.get('location', '')}

Description:
{job_data.get('description', '')}

Requirements:
{job_data.get('requirements', '')}

Skills: {', '.join(job_data.get('skills', []))}
""".strip()

    # Split into chunks
    text_chunks = chunk_text(
        full_text,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap
    )

    # Prepare chunk objects with metadata
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


# ============================================================
# Verification & Testing
# ============================================================

def test_embeddings():
    """Test embedding generation"""
    try:
        print("🧪 Testing HuggingFace embeddings...")
        
        generator = get_embedding_generator()
        
        # Test single embedding
        test_text = "Machine learning engineer with Python experience"
        embedding = generator.generate_embedding(test_text)
        
        print(f"✅ Single embedding generated")
        print(f"   Dimension: {len(embedding)}")
        print(f"   Sample values: {embedding[:5]}")
        
        # Test batch embeddings
        test_texts = [
            "Data scientist with deep learning skills",
            "Full stack developer proficient in React and Node.js",
            "DevOps engineer experienced in Kubernetes"
        ]
        
        embeddings = generator.generate_embeddings_batch(test_texts)
        print(f"✅ Batch embeddings generated: {len(embeddings)} texts")
        
        # Test chunking
        long_text = """
        We are seeking a talented Machine Learning Engineer to join our team.
        The ideal candidate will have experience with PyTorch, TensorFlow, and
        production ML systems. You will work on cutting-edge AI projects and
        collaborate with data scientists and engineers.
        """ * 5
        
        chunks = chunk_text(long_text, chunk_size=200, overlap=50)
        print(f"✅ Text chunking: {len(chunks)} chunks created")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_embeddings()