import psycopg2
try:
    conn = psycopg2.connect("host=127.0.0.1 port=5432 dbname=smartreco_db user=postgres password=smartreco123")
    print("✅ SUCCESS with postgres user!")
    cur = conn.cursor()
    cur.execute("SELECT version()")
    print(cur.fetchone()[0])
    conn.close()
except Exception as e:
    print(f"❌ FAILED: {e}")
