import psycopg2
import json

def test_connection():
    # Load configuration
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    
    db_config = config['database']['development']
    
    print("Testing database connection with these settings:")
    print(f"Host: {db_config['host']}")
    print(f"Port: {db_config['port']}")
    print(f"Database: {db_config['database']}")
    print(f"User: {db_config['user']}")
    
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        print("✅ Database connection successful!")
        
        # Check if tables exist
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print(f"📊 Existing tables: {[table[0] for table in tables]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == '__main__':
    test_connection()