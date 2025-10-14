import psycopg2
import json  # Using json instead of yaml

def init_database():
    # Load configuration from JSON file
    with open('config.json', 'r') as config_file:  # Changed to config.json
        config = json.load(config_file)  # Using json.load instead of yaml.safe_load

    try:
        # Use development configuration
        db_config = config['database']['development']
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        cur = conn.cursor()
        
        # Drop tables if they exist (for clean start)
        print("Dropping existing tables...")
        cur.execute('DROP TABLE IF EXISTS messages CASCADE')
        cur.execute('DROP TABLE IF EXISTS todos CASCADE') 
        cur.execute('DROP TABLE IF EXISTS users CASCADE')
        
        # Create users table
        print("Creating users table...")
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
        print("Creating todos table...")
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
        print("Creating messages table...")
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
        print("Inserting admin user...")
        cur.execute('''
            INSERT INTO users (employee_id, email, password, name, role) 
            VALUES (%s, %s, %s, %s, %s)
        ''', ('ADMIN001', config['admin']['email'], config['admin']['password'], 'Admin User', 'admin'))
        
        # Insert sample employee
        print("Inserting sample employee...")
        cur.execute('''
            INSERT INTO users (employee_id, email, password, name, role) 
            VALUES (%s, %s, %s, %s, %s)
        ''', ('EMP001', 'mavis@maxelo.com', '123admin', 'Mavis', 'employee'))
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    init_database()