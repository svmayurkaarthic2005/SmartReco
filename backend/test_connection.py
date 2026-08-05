"""Test database connection"""
import asyncio
import asyncpg


async def test_connection():
    print("Testing database connection...")
    print("Connecting to: postgresql://smartreco:smartreco123@localhost:5432/smartreco_db")
    
    try:
        # Try to connect
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='smartreco',
            password='smartreco123',
            database='smartreco_db'
        )
        
        # Test query
        version = await conn.fetchval('SELECT version()')
        print(f"✅ Connected successfully!")
        print(f"PostgreSQL version: {version}")
        
        # Close connection
        await conn.close()
        print("✅ Connection closed")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_connection())
