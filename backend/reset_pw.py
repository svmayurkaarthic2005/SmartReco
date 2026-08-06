import asyncio
from sqlalchemy import text
from app.database.base import AsyncSessionLocal
from passlib.context import CryptContext

async def reset_pw():
    pwd_ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')
    hashed = pwd_ctx.hash('test123')
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("UPDATE users SET hashed_password=:h WHERE email=:e"),
            {"h": hashed, "e": "svmayurkaarthic@gmail.com"}
        )
        await db.commit()
        print(f"Password reset to 'test123' (rows affected: {result.rowcount})")

asyncio.run(reset_pw())
