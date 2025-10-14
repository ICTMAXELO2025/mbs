import os
import psycopg2
from urllib.parse import urlparse

def debug_login():
    print("🔍 Debugging Login Process...")
    print("=" * 50)
    
    # Test database connection
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    print("✅ DATABASE_URL found")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url, sslmode='require')
        print("✅ Database connection successful")
        
        cur = conn.cursor()
        
        # Check if tables exist
        print("\n📊 Checking tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        print(f"Tables found: {[table[0] for table in tables]}")
        
        # Check if users table exists and has data
        if 'users' in [table[0] for table in tables]:
            print("\n👥 Checking users table...")
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            print(f"Total users: {user_count}")
            
            # Show all users
            cur.execute("SELECT id, employee_id, email, name, role FROM users")
            users = cur.fetchall()
            print("Users in database:")
            for user in users:
                print(f"  - ID: {user[0]}, EmployeeID: {user[1]}, Email: {user[2]}, Name: {user[3]}, Role: {user[4]}")
            
            # Test admin login query
            print("\n🔐 Testing admin login...")
            test_email = 'admin@maxelo.com'
            test_password = 'admin123'
            
            cur.execute('SELECT * FROM users WHERE email = %s AND password = %s AND role = %s', 
                       (test_email, test_password, 'admin'))
            admin_user = cur.fetchone()
            
            if admin_user:
                print("✅ Admin login test PASSED")
                print(f"   User found: {admin_user[4]} ({admin_user[2]})")
            else:
                print("❌ Admin login test FAILED - no user found")
                print("   Checking if admin user exists with different password...")
                cur.execute("SELECT email, password FROM users WHERE email = %s", (test_email,))
                admin_data = cur.fetchone()
                if admin_data:
                    print(f"   Admin exists but password might be wrong")
                    print(f"   Stored password: {admin_data[1]}")
                else:
                    print("   Admin user not found in database")
            
            # Test employee login query
            print("\n👤 Testing employee login...")
            test_employee_email = 'mavis@maxelo.com'
            test_employee_password = '123admin'
            
            cur.execute('SELECT * FROM users WHERE email = %s AND password = %s AND role = %s', 
                       (test_employee_email, test_employee_password, 'employee'))
            employee_user = cur.fetchone()
            
            if employee_user:
                print("✅ Employee login test PASSED")
                print(f"   User found: {employee_user[4]} ({employee_user[2]})")
            else:
                print("❌ Employee login test FAILED - no user found")
                print("   Checking if employee user exists...")
                cur.execute("SELECT email, password FROM users WHERE email = %s", (test_employee_email,))
                employee_data = cur.fetchone()
                if employee_data:
                    print(f"   Employee exists but password might be wrong")
                    print(f"   Stored password: {employee_data[1]}")
                else:
                    print("   Employee user not found in database")
        
        else:
            print("❌ 'users' table not found!")
            print("💡 You need to run init_db.py to create the tables")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_login()