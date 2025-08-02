import psycopg2
import sys
from urllib.parse import urlparse

def test_connection():
    # Your Supabase connection string
    DATABASE_URL = "postgresql://postgres:JobAppTrack123!@db.gdpirggdsuphgtznfvvk.supabase.co:5432/postgres"
    
    print("Testing connection to Supabase...")
    print(f"Connecting to: db.gdpirggdsuphgtznfvvk.supabase.co:5432")
    
    try:
        # Parse the URL
        parsed = urlparse(DATABASE_URL)
        
        # Try to connect
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path[1:]  # Remove leading slash
        )
        
        print("✅ SUCCESS: Connected to Supabase database!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        print("✅ Connection test completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ CONNECTION FAILED: {e}")
        print("\nPossible solutions:")
        print("1. Check if your Supabase database is RUNNING (not paused)")
        print("2. Go to your Supabase dashboard and resume the database if paused")
        print("3. Wait 1-2 minutes after resuming for the database to fully start")
        print("4. Check if you're on a network that blocks port 5432")
        print("5. Verify your password is correct")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    test_connection() 