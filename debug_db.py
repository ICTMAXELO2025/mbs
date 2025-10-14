import os
import psycopg2
from urllib.parse import urlparse

def debug_database_connection():
    print("🔍 Debugging Database Connection...")
    print("=" * 50)
    
    # Check if DATABASE_URL exists
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable is NOT set!")
        print("Available environment variables:")
        for key, value in os.environ.items():
            if 'DATABASE' in key or 'DB' in key:
                print(f"   {key}: {value}")
        return False
    
    print(f"✅ DATABASE_URL found")
    print(f"📋 DATABASE_URL (first 50 chars): {database_url[:50]}...")
    
    try:
        # Try to parse the URL
        parsed_url = urlparse(database_url)
        print(f"🔗 Parsed URL:")
        print(f"   - Hostname: {parsed_url.hostname}")
        print(f"   - Port: {parsed_url.port}")
        print(f"   - Database: {parsed_url.path[1:]}")
        print(f"   - Username: {parsed_url.username}")
        
        # Try connection without sslmode first
        print("\n🔄 Testing connection without sslmode...")
        try:
            conn = psycopg2.connect(database_url)
            print("✅ Connection successful without sslmode!")
            conn.close()
        except Exception as e1:
            print(f"❌ Failed without sslmode: {e1}")
            
            # Try with sslmode
            print("\n🔄 Testing connection with sslmode=require...")
            try:
                conn = psycopg2.connect(database_url, sslmode='require')
                print("✅ Connection successful with sslmode=require!")
                conn.close()
            except Exception as e2:
                print(f"❌ Failed with sslmode=require: {e2}")
                
                # Try with sslmode=prefer
                print("\n🔄 Testing connection with sslmode=prefer...")
                try:
                    conn = psycopg2.connect(database_url, sslmode='prefer')
                    print("✅ Connection successful with sslmode=prefer!")
                    conn.close()
                except Exception as e3:
                    print(f"❌ Failed with sslmode=prefer: {e3}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False

if __name__ == '__main__':
    debug_database_connection()