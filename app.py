import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from datetime import datetime

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

def get_db_connection():
    try:
        # Get DATABASE_URL from environment (Render provides this automatically)
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            print("🔗 Using DATABASE_URL from environment")
            # For Render PostgreSQL
            conn = psycopg2.connect(database_url, sslmode='require')
            return conn
        else:
            print("🔗 Using local development database")
            # Local development fallback
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
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        
        try:
            # Check if users table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                print("🔄 Initializing database tables...")
                
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
                print("✅ Database tables created successfully!")
            else:
                print("✅ Database tables already exist.")
                
        except Exception as e:
            print(f"❌ Error during database initialization: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    else:
        print("❌ Could not connect to database for initialization")

# [Keep all your routes the same as before]
@app.route('/')
def index():
    return render_template('base.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT * FROM users WHERE email = %s AND password = %s AND role = %s', 
                           (email, password, 'admin'))
                user = cur.fetchone()
                cur.close()
                conn.close()
                
                if user:
                    session['user_id'] = user[0]
                    session['email'] = user[2]
                    session['role'] = user[5]
                    session['name'] = user[4]
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Invalid admin credentials')
            except Exception as e:
                flash('Database error during login')
                print(f"Login error: {e}")
        else:
            flash('Database connection error - please check configuration')
    
    return render_template('admin/login.html')

@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT * FROM users WHERE email = %s AND password = %s AND role = %s', 
                           (email, password, 'employee'))
                user = cur.fetchone()
                cur.close()
                conn.close()
                
                if user:
                    session['user_id'] = user[0]
                    session['email'] = user[2]
                    session['role'] = user[5]
                    session['name'] = user[4]
                    return redirect(url_for('employee_dashboard'))
                else:
                    flash('Invalid employee credentials')
            except Exception as e:
                flash('Database error during login')
                print(f"Login error: {e}")
        else:
            flash('Database connection error - please check configuration')
    
    return render_template('employee/login.html')

# [Include all your other routes - dashboard, todos, messages, profile, etc.]

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
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
    else:
        flash('Database connection error')
        return redirect(url_for('admin_login'))

@app.route('/employee/dashboard')
def employee_dashboard():
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('employee_login'))
    
    conn = get_db_connection()
    if conn:
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
    else:
        flash('Database connection error')
        return redirect(url_for('employee_login'))

# Todo routes
@app.route('/add_todo', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    task = request.form['task']
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO todos (user_id, task) VALUES (%s, %s)', (session['user_id'], task))
        conn.commit()
        cur.close()
        conn.close()
        flash('Todo added successfully')
    else:
        flash('Database connection error')
    
    return redirect(url_for(f"{session['role']}_dashboard"))

@app.route('/toggle_todo/<int:todo_id>')
def toggle_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('UPDATE todos SET completed = NOT completed WHERE id = %s AND user_id = %s', 
                   (todo_id, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()
    
    return redirect(url_for(f"{session['role']}_dashboard"))

@app.route('/delete_todo/<int:todo_id>')
def delete_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM todos WHERE id = %s AND user_id = %s', (todo_id, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()
        flash('Todo deleted successfully')
    
    return redirect(url_for(f"{session['role']}_dashboard"))

# Employee management routes (Admin only)
@app.route('/admin/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute('''
                    INSERT INTO users (employee_id, name, email, password, role) 
                    VALUES (%s, %s, %s, %s, 'employee')
                ''', (employee_id, name, email, password))
                conn.commit()
                flash('Employee added successfully')
            except psycopg2.IntegrityError:
                flash('Employee ID or email already exists')
            finally:
                cur.close()
                conn.close()
            
            return redirect(url_for('manage_employees'))
    
    return render_template('admin/add_employee.html')

@app.route('/admin/manage_employees')
def manage_employees():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT id, employee_id, name, email, created_at FROM users WHERE role = %s ORDER BY created_at DESC', ('employee',))
        employees = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('admin/manage_employees.html', employees=employees)
    else:
        flash('Database connection error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_employee/<int:employee_id>')
def delete_employee(employee_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE id = %s AND role = %s', (employee_id, 'employee'))
        conn.commit()
        cur.close()
        conn.close()
        flash('Employee deleted successfully')
    
    return redirect(url_for('manage_employees'))

# Message routes
@app.route('/admin/send_message', methods=['GET', 'POST'])
def admin_send_message():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        
        if request.method == 'POST':
            receiver_id = request.form['receiver_id']
            subject = request.form['subject']
            message = request.form['message']
            
            if receiver_id == 'all':
                # Send to all employees
                cur.execute('SELECT id FROM users WHERE role = %s', ('employee',))
                employees = cur.fetchall()
                for employee in employees:
                    cur.execute('''
                        INSERT INTO messages (sender_id, receiver_id, subject, message) 
                        VALUES (%s, %s, %s, %s)
                    ''', (session['user_id'], employee[0], subject, message))
            else:
                cur.execute('''
                    INSERT INTO messages (sender_id, receiver_id, subject, message) 
                    VALUES (%s, %s, %s, %s)
                ''', (session['user_id'], receiver_id, subject, message))
            
            conn.commit()
            flash('Message sent successfully')
            return redirect(url_for('admin_dashboard'))
        
        # Get employees for dropdown
        cur.execute('SELECT id, name, email FROM users WHERE role = %s', ('employee',))
        employees = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('admin/send_message.html', employees=employees)
    else:
        flash('Database connection error')
        return redirect(url_for('admin_dashboard'))

@app.route('/employee/send_message', methods=['GET', 'POST'])
def employee_send_message():
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('employee_login'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        
        if request.method == 'POST':
            receiver_id = request.form['receiver_id']
            subject = request.form['subject']
            message = request.form['message']
            
            cur.execute('''
                INSERT INTO messages (sender_id, receiver_id, subject, message) 
                VALUES (%s, %s, %s, %s)
            ''', (session['user_id'], receiver_id, subject, message))
            
            conn.commit()
            flash('Message sent successfully')
            return redirect(url_for('employee_dashboard'))
        
        # Get recipients (admin and other employees)
        cur.execute('SELECT id, name, role FROM users WHERE id != %s', (session['user_id'],))
        recipients = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('employee/send_message.html', recipients=recipients)
    else:
        flash('Database connection error')
        return redirect(url_for('employee_dashboard'))

@app.route('/inbox')
def inbox():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        
        # Mark messages as read when viewing inbox
        cur.execute('UPDATE messages SET is_read = TRUE WHERE receiver_id = %s', (session['user_id'],))
        
        # Get received messages
        cur.execute('''
            SELECT m.*, u.name as sender_name 
            FROM messages m 
            JOIN users u ON m.sender_id = u.id 
            WHERE m.receiver_id = %s 
            ORDER BY m.created_at DESC
        ''', (session['user_id'],))
        messages = cur.fetchall()
        
        conn.commit()
        cur.close()
        conn.close()
        
        template = f"{session['role']}/inbox.html"
        return render_template(template, messages=messages)
    else:
        flash('Database connection error')
        return redirect(url_for(f"{session['role']}_dashboard"))

# Profile routes
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        template = f"{session['role']}/profile.html"
        return render_template(template, user=user)
    else:
        flash('Database connection error')
        return redirect(url_for(f"{session['role']}_dashboard"))

# Password reset route
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        employee_id = request.form['employee_id']
        new_password = request.form['new_password']
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE email = %s AND employee_id = %s', (email, employee_id))
            user = cur.fetchone()
            
            if user:
                cur.execute('UPDATE users SET password = %s WHERE email = %s', (new_password, email))
                conn.commit()
                flash('Password reset successfully')
                cur.close()
                conn.close()
                return redirect(url_for('index'))
            else:
                flash('Invalid email or employee ID')
        
        cur.close()
        conn.close()
    
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)