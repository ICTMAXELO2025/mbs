import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import traceback

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

def get_db_connection():
    """Get database connection with error handling"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not found")
            return None
            
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def initialize_database():
    """FORCE initialize database tables and data"""
    print("🚀 FORCE INITIALIZING DATABASE...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return False
        
    try:
        cur = conn.cursor()
        
        # Drop and recreate all tables
        print("🔄 Creating database tables...")
        
        cur.execute('DROP TABLE IF EXISTS messages CASCADE')
        cur.execute('DROP TABLE IF EXISTS todos CASCADE') 
        cur.execute('DROP TABLE IF EXISTS users CASCADE')
        
        # Create users table
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
        cur.execute('''
            INSERT INTO users (employee_id, email, password, name, role) 
            VALUES (%s, %s, %s, %s, %s)
        ''', ('ADMIN001', 'admin@maxelo.com', 'admin123', 'Admin User', 'admin'))
        
        # Insert sample employee
        cur.execute('''
            INSERT INTO users (employee_id, email, password, name, role) 
            VALUES (%s, %s, %s, %s, %s)
        ''', ('EMP001', 'mavis@maxelo.com', '123admin', 'Mavis', 'employee'))
        
        conn.commit()
        
        # Verify creation
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        
        cur.execute("SELECT email, name, role FROM users")
        users = cur.fetchall()
        
        print(f"✅ Database initialized successfully!")
        print(f"📊 Users created: {user_count}")
        for user in users:
            print(f"   - {user[0]} ({user[1]} - {user[2]})")
            
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        traceback.print_exc()
        conn.rollback()
        return False

# Initialize database on startup
print("=" * 60)
print("🚀 WORK MANAGEMENT APP STARTING...")
print("=" * 60)

# Force database initialization
if initialize_database():
    print("🎉 DATABASE READY - App is starting...")
else:
    print("⚠️ DATABASE INITIALIZATION FAILED - App may not work properly")

print("=" * 60)

# Routes
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        print(f"🔐 Admin login attempt: {email}")
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                print(f"🔄 Executing query for: {email}")
                
                cur.execute('SELECT * FROM users WHERE email = %s AND password = %s AND role = %s', 
                           (email, password, 'admin'))
                user = cur.fetchone()
                
                if user:
                    print(f"✅ Login successful for: {user[4]}")
                    session['user_id'] = user[0]
                    session['email'] = user[2]
                    session['role'] = user[5]
                    session['name'] = user[4]
                    
                    cur.close()
                    conn.close()
                    return redirect(url_for('admin_dashboard'))
                else:
                    print(f"❌ Login failed for: {email}")
                    flash('Invalid admin credentials')
                
                cur.close()
                conn.close()
                
            except Exception as e:
                print(f"❌ Database error during login: {e}")
                # If table doesn't exist, try to initialize
                if "relation \"users\" does not exist" in str(e):
                    print("🔄 Users table missing - attempting to initialize database...")
                    if initialize_database():
                        flash('Database was reset - please try logging in again')
                    else:
                        flash('Database initialization failed - please contact administrator')
                else:
                    flash('Database error during login - please try again')
        else:
            flash('Database connection error - please check configuration')
    
    return render_template('admin/login.html')

@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        print(f"🔐 Employee login attempt: {email}")
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                print(f"🔄 Executing query for: {email}")
                
                cur.execute('SELECT * FROM users WHERE email = %s AND password = %s AND role = %s', 
                           (email, password, 'employee'))
                user = cur.fetchone()
                
                if user:
                    print(f"✅ Login successful for: {user[4]}")
                    session['user_id'] = user[0]
                    session['email'] = user[2]
                    session['role'] = user[5]
                    session['name'] = user[4]
                    
                    cur.close()
                    conn.close()
                    return redirect(url_for('employee_dashboard'))
                else:
                    print(f"❌ Login failed for: {email}")
                    flash('Invalid employee credentials')
                
                cur.close()
                conn.close()
                
            except Exception as e:
                print(f"❌ Database error during login: {e}")
                # If table doesn't exist, try to initialize
                if "relation \"users\" does not exist" in str(e):
                    print("🔄 Users table missing - attempting to initialize database...")
                    if initialize_database():
                        flash('Database was reset - please try logging in again')
                    else:
                        flash('Database initialization failed - please contact administrator')
                else:
                    flash('Database error during login - please try again')
        else:
            flash('Database connection error - please check configuration')
    
    return render_template('employee/login.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        employee_id = request.form['employee_id']
        new_password = request.form['new_password']
        
        print(f"🔑 Password reset attempt for: {email}")
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT * FROM users WHERE email = %s AND employee_id = %s', (email, employee_id))
                user = cur.fetchone()
                
                if user:
                    cur.execute('UPDATE users SET password = %s WHERE email = %s', (new_password, email))
                    conn.commit()
                    print(f"✅ Password reset successful for: {email}")
                    flash('Password reset successfully! You can now login with your new password.')
                    cur.close()
                    conn.close()
                    return redirect(url_for('index'))
                else:
                    print(f"❌ Password reset failed - invalid credentials for: {email}")
                    flash('Invalid email or employee ID')
                
                cur.close()
                conn.close()
                
            except Exception as e:
                print(f"❌ Database error during password reset: {e}")
                flash('Database error during password reset')
        else:
            flash('Database connection error')
    
    return render_template('reset_password.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Get todos
            cur.execute('SELECT * FROM todos WHERE user_id = %s ORDER BY created_at DESC', (session['user_id'],))
            todos = cur.fetchall()
            
            # Get unread messages count
            cur.execute('SELECT COUNT(*) FROM messages WHERE receiver_id = %s AND is_read = FALSE', (session['user_id'],))
            unread_count = cur.fetchone()[0]
            
            # Get employees count
            cur.execute('SELECT COUNT(*) FROM users WHERE role = %s', ('employee',))
            employees_count = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return render_template('admin/dashboard.html', 
                                 todos=todos, 
                                 unread_count=unread_count,
                                 employees_count=employees_count)
        except Exception as e:
            flash('Error loading dashboard')
            print(f"Dashboard error: {e}")
    else:
        flash('Database connection error')
    
    return redirect(url_for('admin_login'))

@app.route('/employee/dashboard')
def employee_dashboard():
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('employee_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Get todos
            cur.execute('SELECT * FROM todos WHERE user_id = %s ORDER BY created_at DESC', (session['user_id'],))
            todos = cur.fetchall()
            
            # Get unread messages count
            cur.execute('SELECT COUNT(*) FROM messages WHERE receiver_id = %s AND is_read = FALSE', (session['user_id'],))
            unread_count = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return render_template('employee/dashboard.html', todos=todos, unread_count=unread_count)
        except Exception as e:
            flash('Error loading dashboard')
            print(f"Dashboard error: {e}")
    else:
        flash('Database connection error')
    
    return redirect(url_for('employee_login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)