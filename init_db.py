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

def init_database():
    """Initialize the database with all required tables and data"""
    print("🚀 DATABASE INITIALIZATION STARTED")
    print("=" * 60)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return False
    
    try:
        cur = conn.cursor()
        
        # Check which database we're using
        cur.execute("SELECT current_database(), version()")
        db_info = cur.fetchone()
        print(f"📊 Initializing database: {db_info[0]}")
        print(f"🔧 PostgreSQL: {db_info[1].split(',')[0]}")
        
        # Drop existing tables (clean start)
        print("\n🗑️  Cleaning existing tables...")
        tables_to_drop = ['messages', 'todos', 'users']
        for table in tables_to_drop:
            try:
                cur.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
                print(f"   ✅ Dropped table: {table}")
            except Exception as e:
                print(f"   ❌ Failed to drop {table}: {e}")
        
        # Create tables
        print("\n📊 Creating database tables...")
        
        # Users table
        print("   Creating 'users' table...")
        cur.execute('''
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                employee_id VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                name VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'employee')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✅ 'users' table created")
        
        # Todos table
        print("   Creating 'todos' table...")
        cur.execute('''
            CREATE TABLE todos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                task TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✅ 'todos' table created")
        
        # Messages table with document support
        print("   Creating 'messages' table...")
        cur.execute('''
            CREATE TABLE messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                subject VARCHAR(200),
                message TEXT NOT NULL,
                document_path VARCHAR(300),
                document_filename VARCHAR(300),
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✅ 'messages' table created with document support")
        
        # Insert default users
        print("\n👥 Inserting default users...")
        
        default_users = [
            {
                'employee_id': 'ADMIN001',
                'email': 'admin@maxelo.com',
                'password': 'admin123',
                'name': 'Admin User',
                'role': 'admin'
            },
            {
                'employee_id': 'EMP001', 
                'email': 'mavis@maxelo.com',
                'password': '123admin',
                'name': 'Mavis',
                'role': 'employee'
            },
            {
                'employee_id': 'EMP002', 
                'email': 'john@maxelo.com',
                'password': '123admin',
                'name': 'John Doe',
                'role': 'employee'
            }
        ]
        
        for user in default_users:
            try:
                cur.execute('''
                    INSERT INTO users (employee_id, email, password, name, role) 
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user['employee_id'], user['email'], user['password'], user['name'], user['role']))
                print(f"   ✅ Added user: {user['name']} ({user['email']})")
            except Exception as e:
                print(f"   ❌ Failed to add user {user['email']}: {e}")
        
        # Insert sample data for testing
        print("\n📝 Inserting sample data...")
        
        # Get user IDs for foreign keys
        cur.execute("SELECT id FROM users WHERE email = 'admin@maxelo.com'")
        admin_id = cur.fetchone()[0]
        
        cur.execute("SELECT id FROM users WHERE email = 'mavis@maxelo.com'")
        mavis_id = cur.fetchone()[0]
        
        cur.execute("SELECT id FROM users WHERE email = 'john@maxelo.com'")
        john_id = cur.fetchone()[0]
        
        # Sample todos
        sample_todos = [
            (admin_id, "Review weekly reports", False),
            (admin_id, "Schedule team meeting", True),
            (mavis_id, "Complete project documentation", False),
            (mavis_id, "Submit timesheet", False),
            (john_id, "Prepare client presentation", False)
        ]
        
        for todo in sample_todos:
            try:
                cur.execute('INSERT INTO todos (user_id, task, completed) VALUES (%s, %s, %s)', todo)
                print(f"   ✅ Added todo: {todo[1]}")
            except Exception as e:
                print(f"   ❌ Failed to add todo: {e}")
        
        # Sample messages with document references
        sample_messages = [
            (admin_id, mavis_id, "Welcome to the team!", "Hello Mavis, welcome to Maxelo Technologies! We're excited to have you on board. Please find the employee handbook attached.", None, None),
            (mavis_id, admin_id, "Question about project", "Hi Admin, I have a question about the new project requirements. When would be a good time to discuss?", None, None),
            (admin_id, john_id, "Project Deadline Update", "Hi John, please review the updated project timeline document attached. The deadline has been moved up by one week.", "/sample/path/project_timeline.pdf", "project_timeline.pdf"),
            (john_id, admin_id, "Client Meeting Notes", "Attached are the notes from yesterday's client meeting. Please review and let me know your feedback.", "/sample/path/meeting_notes.docx", "client_meeting_notes.docx")
        ]
        
        for msg in sample_messages:
            try:
                cur.execute('''
                    INSERT INTO messages (sender_id, receiver_id, subject, message, document_path, document_filename) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', msg)
                has_doc = "📎 WITH DOCUMENT" if msg[4] else ""
                print(f"   ✅ Added message: {msg[2]} {has_doc}")
            except Exception as e:
                print(f"   ❌ Failed to add message: {e}")
        
        # Commit all changes
        conn.commit()
        print("\n💾 All changes committed to database")
        
        # Verify the setup
        print("\n🔍 Verifying database setup...")
        
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"   ✅ Users in database: {user_count}")
        
        cur.execute("SELECT COUNT(*) FROM todos")
        todo_count = cur.fetchone()[0]
        print(f"   ✅ Todos in database: {todo_count}")
        
        cur.execute("SELECT COUNT(*) FROM messages")
        message_count = cur.fetchone()[0]
        print(f"   ✅ Messages in database: {message_count}")
        
        # Check messages with documents
        cur.execute("SELECT COUNT(*) FROM messages WHERE document_path IS NOT NULL")
        messages_with_docs = cur.fetchone()[0]
        print(f"   ✅ Messages with documents: {messages_with_docs}")
        
        # Display final user list
        print("\n📋 Final user list:")
        cur.execute("SELECT employee_id, email, name, role FROM users ORDER BY role, name")
        users = cur.fetchall()
        for user in users:
            print(f"   - {user[2]} ({user[1]}) - {user[3]} - ID: {user[0]}")
        
        # Display message statistics
        print("\n💌 Message Statistics:")
        cur.execute('''
            SELECT u.name as sender, COUNT(*) as sent_count,
                   COUNT(m.document_path) as with_documents
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            GROUP BY u.name
        ''')
        msg_stats = cur.fetchall()
        for stat in msg_stats:
            print(f"   - {stat[0]}: {stat[1]} messages sent ({stat[2]} with documents)")
        
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎉 DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
        print("\n📋 Login Credentials:")
        print("   👑 Admin: admin@maxelo.com / admin123")
        print("   👤 Employee 1: mavis@maxelo.com / 123admin")
        print("   👤 Employee 2: john@maxelo.com / 123admin")
        print(f"📊 Database: {db_info[0]}")
        print("\n📎 FEATURES INCLUDED:")
        print("   ✅ User authentication system")
        print("   ✅ Todo management")
        print("   ✅ Messaging with document attachments")
        print("   ✅ File upload/download support")
        print("   ✅ Admin and employee roles")
        print("\n💡 Your application is now ready to use!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ DATABASE INITIALIZATION FAILED: {e}")
        traceback.print_exc()
        return False

def reset_database():
    """Reset the database to initial state"""
    print("🔄 RESETTING DATABASE...")
    return init_database()

if __name__ == '__main__':
    # You can run this with different commands:
    # python init_db.py          # Normal initialization
    # python init_db.py reset    # Force reset
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        print("♻️  FORCE RESET MODE")
        reset_database()
    else:
        init_database()