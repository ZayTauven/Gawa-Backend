import pg8000.native
import sys

# Set encoding
sys.stdout.reconfigure(encoding='utf-8')

print("Diagnosing with pg8000 (Pure Python) - Correct Names...")

def test_conn(db):
    try:
        print(f"Connecting to {db}...")
        con = pg8000.native.Connection(
            user="postgres",
            password="admin",
            host="localhost",
            port=5432,
            database=db
        )
        print(f"Success connecting to {db}!")
        con.close()
    except Exception as e:
        print(f"Failed to connect to {db}: {e}")

test_conn("academic_db")
test_conn("archive_db")
test_conn("postgres")
