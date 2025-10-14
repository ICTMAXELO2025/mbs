import os
import psycopg2
from urllib.parse import urlparse

def init_database():
    print("🚀 Starting database initialization...")
    
    # Get DATABASE_URL from environment
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not found!")
        print("Please set DATABASE_URL environment variable")
        return False
    
    print("✅ DATABASE_URL found")
    
    try:
        # Connect to Render PostgreSQL
        conn = psycopg2.connect(database_url, sslmode='require')
        print("✅ Connected to database successfully!")
        
        cur = conn.cursor()
        
        # Drop tables if they exist (for clean start)
        print("🔄 Dropping existing tables...")
        cur.execute('DROP TABLE IF EXISTS messages CASCADE')
        cur.execute('DROP TABLE IF EXISTS todos CASCADE') 
        cur.execute('DROP TABLE IF EXISTS users CASCADE')
        
        # Create users table
        print("🔄 Creating users table...")
        cur.execute('''
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                employee_id VARCHAR(50) UNIQUE,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                name VARCHAR(100) NOT NULL,
                role VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create todos table
        print("🔄 Creating todos table...")
        cur.execute('''
            CREATE TABLE todos (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                task TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create messages table
        print("🔄 Creating messages table...")
        cur.execute('''
            CREATE TABLE messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER REFERENCES users(id),
                receiver_id INTEGER REFERENCES users(id),
                subject VARCHAR(200),
                message TEXT NOT NULL,
                document_path VARCHAR(300),
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert admin user
        print("🔄 Inserting admin user...")
        cur.execute('''
            INSERT INTO users (employee_id, email, password, name, role) 
            VALUES (%s, %s, %s, %s, %s)
        ''', ('ADMIN001', 'admin@maxelo.com', 'admin123', 'Admin User', 'admin'))
        
        # Insert sample employee
        print("🔄 Inserting sample employee...")
        cur.execute('''
            INSERT INTO users (employee_id, email, password, name, role) 
            VALUES (%s, %s, %s, %s, %s)
        ''', ('EMP001', 'mavis@maxelo.com', '123admin', 'Mavis', 'employee'))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ Database initialized successfully!")
        print("📊 Created tables: users, todos, messages")
        print("👤 Default users created:")
        print("   - Admin: admin@maxelo.com / admin123")
        print("   - Employee: mavis@maxelo.com / 123admin")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

if __name__ == '__main__':
    init_database()