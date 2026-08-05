"""Product management API endpoints"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import User, Product, DifficultyLevel, EmbeddingStatus
from app.vector.chroma_client import get_chroma_client, ChromaClient
from app.vector.embedding_service import get_embedding_service, EmbeddingService


router = APIRouter(prefix="/products", tags=["Products"])


class ProductCreate(BaseModel):
    """Schema for product creation"""
    title: str = Field(..., min_length=2, max_length=500)
    description: str = Field(..., min_length=5)
    category: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., ge=0)
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER)
    duration_hours: float = Field(default=10.0, ge=0)
    tags: List[str] = Field(default_factory=list)


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: str
    title: str
    description: str
    category: str
    price: float
    difficulty_level: str
    duration_hours: float
    tags: List[str]
    embedding_status: str
    created_at: str


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="Get list of products"
)
async def get_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> List[ProductResponse]:
    """Get products catalog with optional category and difficulty filters."""
    stmt = select(Product)
    if category and category.lower() != "all":
        stmt = stmt.where(Product.category == category)
    if difficulty and difficulty.lower() != "all":
        try:
            difficulty_enum = DifficultyLevel(difficulty.lower())
            stmt = stmt.where(Product.difficulty_level == difficulty_enum)
        except ValueError:
            pass

    stmt = stmt.offset(skip).limit(limit).order_by(Product.created_at.desc())
    result = await db.execute(stmt)
    products = result.scalars().all()

    return [
        ProductResponse(
            id=str(p.id),
            title=p.title,
            description=p.description,
            category=p.category,
            price=float(p.price),
            difficulty_level=p.difficulty_level.value,
            duration_hours=float(p.duration_hours),
            tags=p.tags or [],
            embedding_status=p.embedding_status.value,
            created_at=p.created_at.isoformat()
        )
        for p in products
    ]


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID"
)
async def get_product_by_id(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    """Get single product by UUID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    return ProductResponse(
        id=str(product.id),
        title=product.title,
        description=product.description,
        category=product.category,
        price=float(product.price),
        difficulty_level=product.difficulty_level.value,
        duration_hours=float(product.duration_hours),
        tags=product.tags or [],
        embedding_status=product.embedding_status.value,
        created_at=product.created_at.isoformat()
    )


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product (Admin only)"
)
async def create_product(
    product_in: ProductCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    chroma_client: ChromaClient = Depends(get_chroma_client)
) -> ProductResponse:
    """Create a new product, generate embedding, and index in ChromaDB."""
    # Create product DB record
    new_product = Product(
        title=product_in.title,
        description=product_in.description,
        category=product_in.category,
        price=product_in.price,
        difficulty_level=product_in.difficulty_level,
        duration_hours=product_in.duration_hours,
        tags=product_in.tags,
        embedding_status=EmbeddingStatus.INDEXED
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    # Generate embedding and store in ChromaDB
    try:
        text = f"{new_product.title}. {new_product.description}"
        embedding = await embedding_service.generate_embedding(text)
        await chroma_client.add_product(
            product_id=str(new_product.id),
            embedding=embedding,
            metadata={
                "title": new_product.title,
                "category": new_product.category,
                "difficulty": new_product.difficulty_level.value,
                "price": float(new_product.price),
                "tags": ",".join(new_product.tags) if isinstance(new_product.tags, list) else str(new_product.tags or "")
            },
            document=text
        )
    except Exception as e:
        print(f"Warning: Failed to index product in ChromaDB: {e}")
        new_product.embedding_status = EmbeddingStatus.FAILED
        await db.commit()

    return ProductResponse(
        id=str(new_product.id),
        title=new_product.title,
        description=new_product.description,
        category=new_product.category,
        price=new_product.price,
        difficulty_level=new_product.difficulty_level.value,
        duration_hours=new_product.duration_hours,
        tags=new_product.tags,
        embedding_status=new_product.embedding_status.value,
        created_at=new_product.created_at.isoformat()
    )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a product (Admin only)"
)
async def delete_product(
    product_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    chroma_client: ChromaClient = Depends(get_chroma_client)
):
    """Delete product from PostgreSQL and ChromaDB."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

    # Delete from ChromaDB
    try:
        await chroma_client.delete_product(str(product_id))
    except Exception as e:
        print(f"Warning: Failed to delete product from ChromaDB: {e}")

    # Delete from DB
    await db.delete(product)
    await db.commit()

    return {"message": "Product deleted successfully", "product_id": str(product_id)}
