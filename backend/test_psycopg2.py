"""Test connection with psycopg2 (sync)"""
import psycopg2

print("Testing database connection with psycopg2...")
print("Connecting to: postgresql://smartreco:smartreco123@localhost:5432/smartreco_db")

try:
    # Try to connect
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        user='smartreco',
        password='smartreco123',
        database='smartreco_db'
    )
    
    cur = conn.cursor()
    cur.execute('SELECT version()')
    version = cur.fetchone()[0]
    print(f"✅ Connected successfully!")
    print(f"PostgreSQL version: {version}")
    
    cur.close()
    conn.close()
    print("✅ Connection closed")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    raise
