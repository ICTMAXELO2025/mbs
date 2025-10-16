import os
import psycopg2
from urllib.parse import urlparse
import traceback

def get_db_connection():
    """Get database connection with support for both local PostgreSQL and Render"""
    try:
        # First, try to use Render database (production)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Render PostgreSQL - use the provided DATABASE_URL
            print("🔗 Using Render PostgreSQL database")
            conn = psycopg2.connect(database_url, sslmode='require')
            return conn
        else:
            # Fallback to local PostgreSQL development database
            print("🔗 Using local PostgreSQL database")
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='managament_db',
                user='postgres',
                password='Maxelo@2023'
            )
            return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def debug_database_connection():
    """Comprehensive database debugging"""
    print("🔍 DATABASE DEBUG STARTED")
    print("=" * 60)
    
    # Check environment variables
    print("📋 Checking environment variables...")
    database_url = os.environ.get('DATABASE_URL')
    secret_key = os.environ.get('SECRET_KEY')
    
    print(f"   DATABASE_URL: {'✅ Found' if database_url else '❌ Missing'}")
    print(f"   SECRET_KEY: {'✅ Found' if secret_key else '❌ Missing'}")
    
    if database_url:
        # Parse and display database info (masked for security)
        try:
            parsed = urlparse(database_url)
            print(f"🔗 Render Database Info:")
            print(f"   - Host: {parsed.hostname}")
            print(f"   - Port: {parsed.port}")
            print(f"   - Database: {parsed.path[1:]}")
            print(f"   - Username: {parsed.username}")
            print(f"   - Password: {'*' * 8} (hidden for security)")
        except Exception as e:
            print(f"❌ Error parsing DATABASE_URL: {e}")
    else:
        print("🔗 Local Database Info:")
        print(f"   - Host: localhost")
        print(f"   - Port: 5432") 
        print(f"   - Database: managament_db")
        print(f"   - Username: postgres")
        print(f"   - Password: Maxelo@2023")
    
    # Test connection
    print("\n🔄 Testing database connection...")
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed!")
        return False
        
    try:
        cur = conn.cursor()
        
        # Check which database we're using
        cur.execute("SELECT current_database(), version()")
        db_info = cur.fetchone()
        print(f"✅ Database connection successful!")
        print(f"📊 Connected to: {db_info[0]}")
        print(f"🔧 PostgreSQL: {db_info[1].split(',')[0]}")
        
        # Check tables
        print("\n📊 Checking database tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [table[0] for table in cur.fetchall()]
        
        if tables:
            print(f"✅ Found {len(tables)} table(s):")
            for table in tables:
                print(f"   - {table}")
        else:
            print("❌ No tables found in database")
        
        # Check table structures
        print("\n🏗️  Checking table structures...")
        for table in tables:
            cur.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            print(f"   📋 {table} table columns:")
            for col in columns:
                print(f"      - {col[0]} ({col[1]}, nullable: {col[2]})")
        
        # Check users table specifically
        if 'users' in tables:
            print("\n👥 Checking users table data...")
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            print(f"   Total users: {user_count}")
            
            if user_count > 0:
                cur.execute("SELECT id, employee_id, email, name, role FROM users ORDER BY id")
                users = cur.fetchall()
                print("   User details:")
                for user in users:
                    print(f"     ID: {user[0]}, EmployeeID: {user[1]}, Email: {user[2]}, Name: {user[3]}, Role: {user[4]}")
            else:
                print("   ❌ No users in database")
        else:
            print("❌ 'users' table not found")
        
        # Check messages table with document support
        if 'messages' in tables:
            print("\n💌 Checking messages table (with document support)...")
            cur.execute("SELECT COUNT(*) FROM messages")
            message_count = cur.fetchone()[0]
            print(f"   Total messages: {message_count}")
            
            cur.execute("SELECT COUNT(*) FROM messages WHERE document_path IS NOT NULL")
            messages_with_docs = cur.fetchone()[0]
            print(f"   Messages with documents: {messages_with_docs}")
            
            if message_count > 0:
                cur.execute('''
                    SELECT m.id, u1.name as sender, u2.name as receiver, 
                           m.subject, m.document_filename, m.created_at
                    FROM messages m
                    JOIN users u1 ON m.sender_id = u1.id
                    JOIN users u2 ON m.receiver_id = u2.id
                    ORDER BY m.created_at DESC
                    LIMIT 5
                ''')
                recent_messages = cur.fetchall()
                print("   Recent messages:")
                for msg in recent_messages:
                    has_doc = f"📎 {msg[4]}" if msg[4] else "No attachment"
                    print(f"     #{msg[0]}: '{msg[3]}' | From: {msg[1]} → To: {msg[2]} | {has_doc}")
        
        # Check todos table
        if 'todos' in tables:
            cur.execute("SELECT COUNT(*) FROM todos")
            todo_count = cur.fetchone()[0]
            print(f"   Total todos: {todo_count}")
        
        # Test login queries
        print("\n🔐 Testing login functionality...")
        
        # Test admin login
        cur.execute("SELECT * FROM users WHERE email = 'admin@maxelo.com' AND password = 'admin123' AND role = 'admin'")
        admin = cur.fetchone()
        if admin:
            print("✅ Admin login test: SUCCESS")
            print(f"   Admin user: {admin[4]} ({admin[2]})")
        else:
            print("❌ Admin login test: FAILED")
            # Check why it failed
            cur.execute("SELECT email, password, role FROM users WHERE email = 'admin@maxelo.com'")
            admin_data = cur.fetchone()
            if admin_data:
                print(f"   Admin exists but credentials don't match")
                print(f"   Stored - Email: {admin_data[0]}, Password: {admin_data[1]}, Role: {admin_data[2]}")
            else:
                print("   Admin user not found in database")
        
        # Test employee login
        cur.execute("SELECT * FROM users WHERE email = 'mavis@maxelo.com' AND password = '123admin' AND role = 'employee'")
        employee = cur.fetchone()
        if employee:
            print("✅ Employee login test: SUCCESS")
            print(f"   Employee user: {employee[4]} ({employee[2]})")
        else:
            print("❌ Employee login test: FAILED")
            # Check why it failed
            cur.execute("SELECT email, password, role FROM users WHERE email = 'mavis@maxelo.com'")
            employee_data = cur.fetchone()
            if employee_data:
                print(f"   Employee exists but credentials don't match")
                print(f"   Stored - Email: {employee_data[0]}, Password: {employee_data[1]}, Role: {employee_data[2]}")
            else:
                print("   Employee user not found in database")
        
        # Test document-related queries
        print("\n📎 Testing document functionality...")
        cur.execute('''
            SELECT m.id, m.document_filename, m.document_path, u.name as sender
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.document_path IS NOT NULL
            LIMIT 3
        ''')
        documents = cur.fetchall()
        if documents:
            print("✅ Documents found in database:")
            for doc in documents:
                print(f"   Message #{doc[0]}: '{doc[1]}' from {doc[3]}")
                print(f"     Path: {doc[2]}")
        else:
            print("   No documents found in messages")
        
        cur.close()
        conn.close()
        print("\n🎉 Database debug completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return False

def test_specific_queries():
    """Test specific queries that might be failing"""
    print("\n🧪 Testing specific queries...")
    
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        queries = [
            "SELECT version()",  # PostgreSQL version
            "SELECT current_database()",  # Current database name
            "SELECT current_user",  # Current user
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'",  # Table count
            # Test message queries with document fields
            "SELECT COUNT(*) FROM messages WHERE document_filename IS NOT NULL",
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'messages' AND column_name IN ('document_path', 'document_filename')",
        ]
        
        for query in queries:
            try:
                cur.execute(query)
                result = cur.fetchone()[0]
                print(f"✅ {query}: {result}")
            except Exception as e:
                print(f"❌ Query failed: {query}")
                print(f"   Error: {e}")
        
        # Test document column existence
        print("\n🔍 Checking document-related columns in messages table:")
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'messages' 
            AND column_name IN ('document_path', 'document_filename')
        """)
        doc_columns = cur.fetchall()
        if doc_columns:
            for col in doc_columns:
                print(f"✅ {col[0]}: {col[1]} (nullable: {col[2]})")
        else:
            print("❌ Document columns not found in messages table")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during query testing: {e}")

if __name__ == '__main__':
    print("🚀 Starting comprehensive database debug...")
    print("=" * 60)
    
    success = debug_database_connection()
    
    if not success:
        print("\n🔧 Running additional diagnostics...")
        test_specific_queries()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ DEBUG COMPLETED - Database appears to be working correctly")
        print("📎 Document support: ✅ Available")
        print("💡 If you're still having issues, check your application code")
    else:
        print("❌ DEBUG COMPLETED - Database issues found")
        print("💡 Check the errors above and fix the configuration")