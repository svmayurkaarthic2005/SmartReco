"""
Script to generate embeddings for all products in the database.
"""

import asyncio
import sys
from sqlalchemy import select

from app.database.base import AsyncSessionLocal
from app.models.product import Product, EmbeddingStatus
from app.vector.embedding_service import get_embedding_service
from app.vector.chroma_client import get_chroma_client


async def generate_all_embeddings():
    """Generate embeddings for all products"""
    
    print("🚀 Starting embedding generation...")
    
    # Initialize services
    embedding_service = get_embedding_service()
    chroma_client = get_chroma_client()
    
    # Get database session
    async with AsyncSessionLocal() as session:
        try:
            # Fetch all products
            stmt = select(Product)
            result = await session.execute(stmt)
            products = result.scalars().all()
            
            if not products:
                print("❌ No products found in database")
                return
            
            print(f"📦 Found {len(products)} products")
            
            # Prepare batch data
            product_ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            print("🔄 Generating embeddings...")
            success_count = 0
            failed_count = 0
            
            for i, product in enumerate(products, 1):
                try:
                    # Generate text representation
                    text = f"{product.title}. {product.description}"
                    
                    # Generate embedding
                    embedding = await embedding_service.generate_embedding(text)
                    
                    # Prepare metadata (ChromaDB only supports str, int, float, bool)
                    metadata = {
                        "title": product.title,
                        "category": product.category,
                        "difficulty": product.difficulty_level.value,
                        "price": float(product.price),
                        "tags": ",".join(product.tags) if product.tags else ""
                    }
                    
                    # Add to batch
                    product_ids.append(str(product.id))
                    embeddings.append(embedding)
                    metadatas.append(metadata)
                    documents.append(text)
                    
                    # Update status in database
                    product.embedding_status = EmbeddingStatus.INDEXED
                    
                    success_count += 1
                    print(f"  ✓ [{i}/{len(products)}] {product.title[:50]}")
                    
                except Exception as e:
                    print(f"  ✗ [{i}/{len(products)}] Failed: {product.title[:50]} - {e}")
                    product.embedding_status = EmbeddingStatus.FAILED
                    failed_count += 1
            
            # Add all embeddings to ChromaDB in batch
            if product_ids:
                print(f"\n📥 Adding {len(product_ids)} embeddings to ChromaDB...")
                await chroma_client.add_products_batch(
                    product_ids=product_ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
            
            # Commit database updates
            await session.commit()
            
            # Check collection count
            count = chroma_client.get_collection_count()
            
            print(f"\n✅ Embedding generation complete!")
            print(f"   - Successfully indexed: {success_count}")
            print(f"   - Failed: {failed_count}")
            print(f"   - ChromaDB collection count: {count}")
            
        except Exception as e:
            print(f"\n❌ Error during embedding generation: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(generate_all_embeddings())
