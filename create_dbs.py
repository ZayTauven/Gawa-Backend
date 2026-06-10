import pg8000.native
import sys

# Set encoding
sys.stdout.reconfigure(encoding='utf-8')

print("Attempting to create databases...")

try:
    # Connect to the default 'postgres' database to perform administrative tasks
    con = pg8000.native.Connection(
        user="postgres",
        password="admin",
        host="localhost",
        port=5432,
        database="postgres"
    )
    
    # Check existing DBs again
    existing_dbs = [row[0] for row in con.run("SELECT datname FROM pg_database")]
    print(f"Current databases: {existing_dbs}")

    for db in ["academic_db", "archive_db"]:
        if db not in existing_dbs:
            print(f"Creating database {db}...")
            # Autocommit is handled by running outside of a block if needed, 
            # but pg8000 native run executes immediately.
            # However, CREATE DATABASE cannot run inside a transaction block.
            # pg8000.native.Connection is always in 'autocommit' mode for simple .run() calls unless a transaction is started.
            try:
                con.run(f"CREATE DATABASE {db}")
                print(f"Database {db} created successfully.")
            except Exception as e:
                print(f"Failed to create {db}: {e}")
        else:
            print(f"Database {db} already exists.")
            
    con.close()
except Exception as e:
    print(f"Administrative connection failed: {e}")
