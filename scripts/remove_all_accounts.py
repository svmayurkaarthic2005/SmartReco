"""
Script to remove all user accounts and associated user data from ALL database instances
(both PostgreSQL from backend/.env and SQLite from root/.env / local db files).
"""

import asyncio
import sys
import os
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import delete, select, func
from app.models import User, Event, Recommendation, RecommendationCache


async def purge_db_url(db_url: str, label: str):
    """Purge users from a specific database URL"""
    print(f"\n[INFO] Connecting to {label} ({db_url})...")
    try:
        engine = create_async_engine(db_url, echo=False)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with session_factory() as session:
            try:
                count_result = await session.execute(select(func.count(User.id)))
                user_count = count_result.scalar() or 0
            except Exception as e:
                print(f"  [SKIP] Could not query {label}: {e}")
                await engine.dispose()
                return

            print(f"  Found {user_count} user account(s) in {label}.")

            if user_count > 0:
                await session.execute(delete(RecommendationCache))
                await session.execute(delete(Recommendation))
                await session.execute(delete(Event))
                await session.execute(delete(User))
                await session.commit()
                print(f"  [SUCCESS] Purged {user_count} user account(s) from {label}!")
            else:
                print(f"  {label} is already empty.")

        await engine.dispose()
    except Exception as e:
        print(f"  [ERROR] Failed to purge {label}: {e}")


async def remove_all_accounts():
    """Remove all user accounts across all database targets"""
    db_urls = []

    # 1. Check backend/.env
    backend_env = backend_dir / ".env"
    if backend_env.exists():
        env_vars = {}
        for line in backend_env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
        if "DATABASE_URL" in env_vars:
            db_urls.append((env_vars["DATABASE_URL"], "backend/.env (PostgreSQL)"))

    # 2. Check root/.env
    root_env = root_dir / ".env"
    if root_env.exists():
        env_vars = {}
        for line in root_env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
        if "DATABASE_URL" in env_vars:
            db_urls.append((env_vars["DATABASE_URL"], "root/.env (SQLite)"))

    # 3. Local SQLite file if present
    root_sqlite = root_dir / "smartreco.db"
    if root_sqlite.exists():
        db_urls.append((f"sqlite+aiosqlite:///{root_sqlite.as_posix()}", "smartreco.db file"))

    # Deduplicate DB URLs
    seen = set()
    for url, label in db_urls:
        if url not in seen:
            seen.add(url)
            await purge_db_url(url, label)


if __name__ == "__main__":
    print("[START] Removing all user accounts from all database instances...")
    asyncio.run(remove_all_accounts())
