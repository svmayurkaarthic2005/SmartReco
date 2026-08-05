import psycopg2
try:
    conn = psycopg2.connect("host=127.0.0.1 port=5432 dbname=smartreco_db user=smartreco password=smartreco123")
    print("✅ SUCCESS")
    conn.close()
except Exception as e:
    print(f"❌ FAILED: {e}")
