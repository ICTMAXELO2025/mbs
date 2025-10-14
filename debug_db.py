import os
import psycopg2
from urllib.parse import urlparse
import traceback

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
    
    if not database_url:
        print("❌ DATABASE_URL environment variable is missing!")
        print("💡 Make sure your database is connected to your web service on Render")
        return False
    
    # Parse and display database info (masked for security)
    try:
        parsed = urlparse(database_url)
        print(f"🔗 Database Info:")
        print(f"   - Host: {parsed.hostname}")
        print(f"   - Port: {parsed.port}")
        print(f"   - Database: {parsed.path[1:]}")
        print(f"   - Username: {parsed.username}")
        print(f"   - Password: {'*' * 8} (hidden for security)")
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
    
    # Test connection
    print("\n🔄 Testing database connection...")
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        print("✅ Database connection successful!")
        
        cur = conn.cursor()
        
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
        
        # Check todos table
        if 'todos' in tables:
            cur.execute("SELECT COUNT(*) FROM todos")
            todo_count = cur.fetchone()[0]
            print(f"   Total todos: {todo_count}")
        
        # Check messages table
        if 'messages' in tables:
            cur.execute("SELECT COUNT(*) FROM messages")
            message_count = cur.fetchone()[0]
            print(f"   Total messages: {message_count}")
        
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
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        cur = conn.cursor()
        
        queries = [
            "SELECT version()",  # PostgreSQL version
            "SELECT current_database()",  # Current database name
            "SELECT current_user",  # Current user
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'",  # Table count
        ]
        
        for query in queries:
            try:
                cur.execute(query)
                result = cur.fetchone()[0]
                print(f"✅ {query}: {result}")
            except Exception as e:
                print(f"❌ Query failed: {query}")
                print(f"   Error: {e}")
        
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
        print("💡 If you're still having issues, check your application code")
    else:
        print("❌ DEBUG COMPLETED - Database issues found")
        print("💡 Check the errors above and fix the configuration")