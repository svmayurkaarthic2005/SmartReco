"""Embedding service for generating vector embeddings"""

import asyncio
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from app.config import settings


class EmbeddingService:
    """
    Service for generating text embeddings using Sentence Transformers.
    
    Uses the model specified in settings (default: all-MiniLM-L6-v2).
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the Sentence Transformers model
                       (default: from settings.embedding_model)
        """
        self.model_name = model_name or settings.embedding_model
        self._model = None
    
    @property
    def model(self):
        """Lazy-load the embedding model"""
        if self._model is None:
            if SentenceTransformer is not None:
                try:
                    print(f"Loading cached embedding model: {self.model_name}")
                    # Try instant local load first (0ms HF network latency)
                    try:
                        self._model = SentenceTransformer(self.model_name, local_files_only=True)
                    except Exception:
                        self._model = SentenceTransformer(self.model_name)
                except Exception as e:
                    print(f"Warning: Could not load SentenceTransformer model: {e}")
            else:
                print("Warning: sentence_transformers not installed, using fallback embeddings.")
        return self._model

    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Example:
            >>> service = EmbeddingService()
            >>> embedding = await service.generate_embedding("Python programming")
            >>> len(embedding)
            384
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * settings.embedding_dimension
        
        if self.model is None:
            return [0.1] * settings.embedding_dimension

        # Run the synchronous encode() in a thread pool so it doesn't block
        # the asyncio event loop. Without this, all other requests (e.g. /products)
        # stall for the full duration of the CPU-bound embedding computation.
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
        )

        # Convert to list of floats
        return embedding.tolist()
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
            
        Example:
            >>> service = EmbeddingService()
            >>> embeddings = await service.generate_embeddings_batch([
            ...     "Python programming",
            ...     "Machine learning"
            ... ])
            >>> len(embeddings)
            2
        """
        if not texts:
            return []
        
        # Filter out empty texts
        non_empty_texts = [t if t and t.strip() else " " for t in texts]

        if self.model is None:
            return [[0.1] * settings.embedding_dimension] * len(non_empty_texts)

        # Run the synchronous batch encode in a thread pool
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                non_empty_texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                batch_size=32
            )
        )

        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.model.get_sentence_embedding_dimension()


# Global instance (singleton pattern)
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get global embedding service instance (singleton).
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
