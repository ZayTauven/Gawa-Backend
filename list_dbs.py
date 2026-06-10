import pg8000.native
import sys

# Set encoding
sys.stdout.reconfigure(encoding='utf-8')

try:
    con = pg8000.native.Connection(
        user="postgres",
        password="admin",
        host="localhost",
        port=5432,
        database="postgres"
    )
    print("Listing databases:")
    for row in con.run("SELECT datname FROM pg_database WHERE datistemplate = false"):
        print(f"- {row[0]}")
    con.close()
except Exception as e:
    print(f"Error: {e}")
