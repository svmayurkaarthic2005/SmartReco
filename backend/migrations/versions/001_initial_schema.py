"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-04 02:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('user', 'admin', name='user_role', native_enum=False), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('difficulty_level', sa.Enum('beginner', 'intermediate', 'advanced', name='difficulty_level', native_enum=False), nullable=False),
        sa.Column('duration_hours', sa.Float(), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('embedding_status', sa.Enum('indexed', 'pending', 'failed', name='embedding_status', native_enum=False), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_difficulty_level'), 'products', ['difficulty_level'], unique=False)
    op.create_index(op.f('ix_products_embedding_status'), 'products', ['embedding_status'], unique=False)
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)
    op.create_index(op.f('ix_products_title'), 'products', ['title'], unique=False)

    # Create events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.Enum(
            'view_product', 'view_category', 'search', 'add_to_cart', 'wishlist', 
            'enroll', 'scroll', 'time_on_page', 'repeat_visit', 'category_switch', 
            'session_end', 'exit', 
            name='event_type', native_enum=False
        ), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('search_query', sa.Text(), nullable=True),
        sa.Column('dwell_time', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_event_type'), 'events', ['event_type'], unique=False)
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)
    op.create_index(op.f('ix_events_product_id'), 'events', ['product_id'], unique=False)
    op.create_index(op.f('ix_events_session_id'), 'events', ['session_id'], unique=False)
    op.create_index(op.f('ix_events_timestamp'), 'events', ['timestamp'], unique=False)
    op.create_index(op.f('ix_events_user_id'), 'events', ['user_id'], unique=False)

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('persona', sa.Text(), nullable=False),
        sa.Column('narrative', sa.Text(), nullable=False),
        sa.Column('product_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendations_generated_at'), 'recommendations', ['generated_at'], unique=False)
    op.create_index(op.f('ix_recommendations_id'), 'recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_recommendations_user_id'), 'recommendations', ['user_id'], unique=False)

    # Create recommendation_cache table
    op.create_table(
        'recommendation_cache',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_hash', sa.String(length=64), nullable=False),
        sa.Column('cached_recommendation', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_recommendation_cache_event_hash'), 'recommendation_cache', ['event_hash'], unique=False)
    op.create_index(op.f('ix_recommendation_cache_expires_at'), 'recommendation_cache', ['expires_at'], unique=False)
    op.create_index(op.f('ix_recommendation_cache_user_id'), 'recommendation_cache', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_recommendation_cache_user_id'), table_name='recommendation_cache')
    op.drop_index(op.f('ix_recommendation_cache_expires_at'), table_name='recommendation_cache')
    op.drop_index(op.f('ix_recommendation_cache_event_hash'), table_name='recommendation_cache')
    op.drop_table('recommendation_cache')
    
    op.drop_index(op.f('ix_recommendations_user_id'), table_name='recommendations')
    op.drop_index(op.f('ix_recommendations_id'), table_name='recommendations')
    op.drop_index(op.f('ix_recommendations_generated_at'), table_name='recommendations')
    op.drop_table('recommendations')
    
    op.drop_index(op.f('ix_events_user_id'), table_name='events')
    op.drop_index(op.f('ix_events_timestamp'), table_name='events')
    op.drop_index(op.f('ix_events_session_id'), table_name='events')
    op.drop_index(op.f('ix_events_product_id'), table_name='events')
    op.drop_index(op.f('ix_events_id'), table_name='events')
    op.drop_index(op.f('ix_events_event_type'), table_name='events')
    op.drop_table('events')
    
    op.drop_index(op.f('ix_products_title'), table_name='products')
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_index(op.f('ix_products_embedding_status'), table_name='products')
    op.drop_index(op.f('ix_products_difficulty_level'), table_name='products')
    op.drop_index(op.f('ix_products_category'), table_name='products')
    op.drop_table('products')
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enums
    sa.Enum(name='embedding_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='difficulty_level').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='event_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)
