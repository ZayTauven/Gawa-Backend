import os
import sys
import django
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

# Force UTF-8 for output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gawa_core.settings')
django.setup()

def check_db(db_name):
    print(f"Checking connection to {db_name}...")
    try:
        conn = connections[db_name]
        conn.connect()
        print(f"Successfully connected to {db_name}!")
    except OperationalError as e:
        print(f"Error connecting to {db_name}: {e}")
    except Exception as e:
        print(f"Unexpected error for {db_name}: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Default encoding: {sys.getdefaultencoding()}")
    check_db('default')
    check_db('archive_db')
