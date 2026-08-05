"""
Product service for managing products and embeddings.

Handles product CRUD operations and ChromaDB embedding generation.
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, EmbeddingStatus
from app.vector.embedding_service import EmbeddingService
from app.vector.chroma_client import ChromaClient


logger = logging.getLogger(__name__)


class ProductService:
    """
    Service for product management and embedding operations.
    
    Features:
    - Retry failed embeddings
    - Batch embedding generation
    - Product CRUD operations
    """
    
    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService,
        chroma_client: ChromaClient
    ):
        """
        Initialize product service.
        
        Args:
            db: Database session
            embedding_service: Embedding generation service
            chroma_client: ChromaDB client
        """
        self.db = db
        self.embedding_service = embedding_service
        self.chroma_client = chroma_client
    
    async def retry_failed_embeddings(self) -> int:
        """
        Retry generating embeddings for products with FAILED status.
        
        Returns:
            Number of products successfully updated
            
        Example:
            >>> service = ProductService(db, embeddings, chroma)
            >>> count = await service.retry_failed_embeddings()
            >>> print(f"Retried {count} products")
        """
        # Query products with FAILED status
        stmt = select(Product).where(
            Product.embedding_status == EmbeddingStatus.FAILED
        ).limit(50)  # Process in batches
        
        result = await self.db.execute(stmt)
        failed_products = result.scalars().all()
        
        if not failed_products:
            logger.info("No failed embeddings to retry")
            return 0
        
        logger.info(f"Retrying embeddings for {len(failed_products)} products")
        
        success_count = 0
        
        for product in failed_products:
            try:
                # Generate embedding
                text = f"{product.title}. {product.description}"
                embedding = await self.embedding_service.generate_embedding(text)
                
                # Add to ChromaDB
                await self.chroma_client.add_product(
                    product_id=str(product.id),
                    title=product.title,
                    description=product.description,
                    embedding=embedding,
                    metadata={
                        "category": product.category,
                        "difficulty": product.difficulty_level.value,
                        "price": product.price,
                        "tags": product.tags
                    }
                )
                
                # Update status
                product.embedding_status = EmbeddingStatus.INDEXED
                success_count += 1
                
                logger.info(f"Successfully indexed product {product.id}: {product.title}")
                
            except Exception as e:
                logger.error(f"Failed to index product {product.id}: {e}")
                # Keep status as FAILED for next retry
        
        # Commit updates
        await self.db.commit()
        
        logger.info(f"Retry complete: {success_count}/{len(failed_products)} successful")
        return success_count
    
    async def index_pending_products(self) -> int:
        """
        Index products with PENDING status.
        
        Returns:
            Number of products successfully indexed
        """
        stmt = select(Product).where(
            Product.embedding_status == EmbeddingStatus.PENDING
        ).limit(100)
        
        result = await self.db.execute(stmt)
        pending_products = result.scalars().all()
        
        if not pending_products:
            return 0
        
        logger.info(f"Indexing {len(pending_products)} pending products")
        
        success_count = 0
        
        for product in pending_products:
            try:
                text = f"{product.title}. {product.description}"
                embedding = await self.embedding_service.generate_embedding(text)
                
                await self.chroma_client.add_product(
                    product_id=str(product.id),
                    title=product.title,
                    description=product.description,
                    embedding=embedding,
                    metadata={
                        "category": product.category,
                        "difficulty": product.difficulty_level.value,
                        "price": product.price,
                        "tags": product.tags
                    }
                )
                
                product.embedding_status = EmbeddingStatus.INDEXED
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to index product {product.id}: {e}")
                product.embedding_status = EmbeddingStatus.FAILED
        
        await self.db.commit()
        
        logger.info(f"Indexed {success_count}/{len(pending_products)} products")
        return success_count
