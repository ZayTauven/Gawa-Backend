import psycopg2
import sys
import os

# Set encoding
sys.stdout.reconfigure(encoding='utf-8')

print(f"PYTHONUTF8: {os.environ.get('PYTHONUTF8')}")
print(f"PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING')}")
print(f"System encoding: {sys.getdefaultencoding()}")
print(f"Filesystem encoding: {sys.getfilesystemencoding()}")

try:
    print("Attempting direct psycopg2 connection to academicdb...")
    conn = psycopg2.connect(
        dbname="academicdb",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )
    print("Success!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
