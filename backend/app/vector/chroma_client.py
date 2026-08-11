"""ChromaDB client wrapper"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


class ChromaClient:
    """
    Wrapper for ChromaDB client with SmartReco-specific operations.
    """
    
    def __init__(self):
        """Initialize ChromaDB client"""
        self._client: Optional[chromadb.HttpClient] = None
        self._collection = None
    
    @property
    def client(self):
        """Lazy-load ChromaDB client with persistent storage"""
        if self._client is None:
            import socket
            is_http_available = False
            try:
                # Fast socket probe (200ms timeout) to check if ChromaDB HTTP server is actually listening
                with socket.create_connection((settings.chroma_host, settings.chroma_port), timeout=0.2):
                    is_http_available = True
            except (OSError, TimeoutError):
                is_http_available = False

            if is_http_available:
                try:
                    import threading
                    print(f"Connecting to ChromaDB HTTP server at {settings.chroma_host}:{settings.chroma_port}")
                    http_client = chromadb.HttpClient(
                        host=settings.chroma_host,
                        port=settings.chroma_port,
                        settings=ChromaSettings(anonymized_telemetry=False)
                    )
                    # Run heartbeat in a background thread so it doesn't block
                    # event loop when this property is first accessed
                    result = []
                    error = []
                    def _hb():
                        try:
                            http_client.heartbeat()
                            result.append(True)
                        except Exception as e:
                            error.append(e)
                    t = threading.Thread(target=_hb, daemon=True)
                    t.start()
                    t.join(timeout=1.0)  # Wait max 1s
                    if error:
                        raise error[0]
                    if not result:
                        raise TimeoutError("ChromaDB heartbeat timed out")
                    self._client = http_client
                    print("✓ ChromaDB HTTP connection successful")
                except Exception as e:
                    print(f"ChromaDB HTTP connection failed: {e}")
                    is_http_available = False

            if not is_http_available or self._client is None:
                print("Using persistent ChromaDB with local storage at ./chroma")
                self._client = chromadb.PersistentClient(
                    path="./chroma",
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
        return self._client

    def get_collection(self):
        """Get or create the products collection"""
        if self._collection is None:
            try:
                self._collection = self.client.get_collection(
                    name=settings.chroma_collection_name
                )
            except Exception:
                # Collection doesn't exist, create it
                self._collection = self.client.create_collection(
                    name=settings.chroma_collection_name,
                    metadata={"description": "SmartReco product embeddings"}
                )
        return self._collection

    async def search_products(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products using vector similarity (executed in thread pool).
        """
        import asyncio
        loop = asyncio.get_running_loop()

        def _do_search():
            collection = self.get_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["metadatas", "distances", "documents"]
            )
            formatted_results = []
            if results and results['ids'] and results['ids'][0]:
                ids = results['ids'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                documents = results['documents'][0] if results['documents'] else []

                for i, product_id in enumerate(ids):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 1.0
                    document = documents[i] if i < len(documents) else ""

                    result = {
                        'id': product_id,
                        'product_id': product_id,
                        'title': metadata.get('title', ''),
                        'description': document or metadata.get('description', ''),
                        'category': metadata.get('category', ''),
                        'difficulty': metadata.get('difficulty', ''),
                        'price': metadata.get('price', 0.0),
                        'tags': metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                        'distance': float(distance),
                        'similarity_score': 1.0 - float(distance)
                    }
                    formatted_results.append(result)
            return formatted_results

        return await loop.run_in_executor(None, _do_search)
    
    async def add_product(
        self,
        product_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        document: str
    ) -> None:
        """
        Add a product to the vector store.
        
        Args:
            product_id: Unique product ID
            embedding: Product embedding vector
            metadata: Product metadata (title, category, etc.)
            document: Product text (title + description)
        """
        collection = self.get_collection()
        
        collection.add(
            ids=[product_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[document]
        )
    
    async def add_products_batch(
        self,
        product_ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: List[str]
    ) -> None:
        """
        Add multiple products in batch.
        
        Args:
            product_ids: List of product IDs
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            documents: List of product texts
        """
        collection = self.get_collection()
        
        collection.add(
            ids=product_ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
    
    async def update_product(
        self,
        product_id: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        document: Optional[str] = None
    ) -> None:
        """
        Update an existing product.
        
        Args:
            product_id: Product ID to update
            embedding: New embedding (optional)
            metadata: New metadata (optional)
            document: New document (optional)
        """
        collection = self.get_collection()
        
        update_params = {'ids': [product_id]}
        
        if embedding is not None:
            update_params['embeddings'] = [embedding]
        if metadata is not None:
            update_params['metadatas'] = [metadata]
        if document is not None:
            update_params['documents'] = [document]
        
        collection.update(**update_params)
    
    async def delete_product(self, product_id: str) -> None:
        """Delete a product from the vector store"""
        collection = self.get_collection()
        collection.delete(ids=[product_id])
    
    def get_collection_count(self) -> int:
        """Get total number of products in collection"""
        collection = self.get_collection()
        return collection.count()


# Global instance (singleton pattern)
_chroma_client: Optional[ChromaClient] = None


def get_chroma_client() -> ChromaClient:
    """
    Get global ChromaDB client instance (singleton).
    
    Returns:
        ChromaClient instance
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
    return _chroma_client
