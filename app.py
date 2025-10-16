import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from datetime import datetime
import traceback
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

def initialize_database():
    """Initialize database tables and data"""
    print("🚀 Initializing database...")
    
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return False
        
    try:
        cur = conn.cursor()
        
        # Check which database we're using
        cur.execute("SELECT current_database()")
        db_name = cur.fetchone()[0]
        print(f"📊 Initializing database: {db_name}")
        
        # Drop and recreate all tables
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
                document_filename VARCHAR(300),
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
        print(f"✅ Database initialized successfully! Users created: {user_count}")
        print(f"📊 Database: {db_name}")
            
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        traceback.print_exc()
        return False

# Initialize database on startup
print("=" * 60)
print("🚀 WORK MANAGEMENT APP STARTING...")
print("=" * 60)

# Check which database we're using
conn = get_db_connection()
if conn:
    cur = conn.cursor()
    cur.execute("SELECT current_database(), version()")
    db_info = cur.fetchone()
    print(f"📊 Connected to: {db_info[0]}")
    print(f"🔧 PostgreSQL: {db_info[1].split(',')[0]}")
    cur.close()
    conn.close()

initialize_database()
print("=" * 60)

# ===== ROUTES =====

@app.route('/')
def index():
    """Home page with login options"""
    return render_template('base.html')

# ===== AUTHENTICATION ROUTES =====

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
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
                
                if user:
                    session['user_id'] = user[0]
                    session['email'] = user[2]
                    session['role'] = user[5]
                    session['name'] = user[4]
                    flash('Login successful!')
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Invalid admin credentials')
                
                cur.close()
                conn.close()
            except Exception as e:
                flash('Database error during login')
        else:
            flash('Database connection error')
    
    return render_template('admin/login.html')

@app.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    """Employee login"""
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
                
                if user:
                    session['user_id'] = user[0]
                    session['email'] = user[2]
                    session['role'] = user[5]
                    session['name'] = user[4]
                    flash('Login successful!')
                    return redirect(url_for('employee_dashboard'))
                else:
                    flash('Invalid employee credentials')
                
                cur.close()
                conn.close()
            except Exception as e:
                flash('Database error during login')
        else:
            flash('Database connection error')
    
    return render_template('employee/login.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Password reset for all users"""
    if request.method == 'POST':
        email = request.form['email']
        employee_id = request.form['employee_id']
        new_password = request.form['new_password']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('SELECT * FROM users WHERE email = %s AND employee_id = %s', (email, employee_id))
                user = cur.fetchone()
                
                if user:
                    cur.execute('UPDATE users SET password = %s WHERE email = %s', (new_password, email))
                    conn.commit()
                    flash('Password reset successfully! You can now login with your new password.')
                    return redirect(url_for('index'))
                else:
                    flash('Invalid email or employee ID')
                
                cur.close()
                conn.close()
            except Exception as e:
                flash('Database error during password reset')
        else:
            flash('Database connection error')
    
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    """Logout all users"""
    session.clear()
    flash('You have been logged out successfully.')
    return redirect(url_for('index'))

# ===== DASHBOARD ROUTES =====

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
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
    else:
        flash('Database connection error')
    
    return redirect(url_for('admin_login'))

@app.route('/employee/dashboard')
def employee_dashboard():
    """Employee dashboard"""
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
    else:
        flash('Database connection error')
    
    return redirect(url_for('employee_login'))

# ===== TODO ROUTES =====

@app.route('/add_todo', methods=['POST'])
def add_todo():
    """Add new todo item"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    task = request.form['task']
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('INSERT INTO todos (user_id, task) VALUES (%s, %s)', (session['user_id'], task))
            conn.commit()
            flash('Todo added successfully!')
        except Exception as e:
            flash('Error adding todo')
        finally:
            cur.close()
            conn.close()
    else:
        flash('Database connection error')
    
    return redirect(url_for(f"{session['role']}_dashboard"))

@app.route('/toggle_todo/<int:todo_id>')
def toggle_todo(todo_id):
    """Toggle todo completion status"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('UPDATE todos SET completed = NOT completed WHERE id = %s AND user_id = %s', 
                       (todo_id, session['user_id']))
            conn.commit()
        except Exception as e:
            flash('Error updating todo')
        finally:
            cur.close()
            conn.close()
    
    return redirect(url_for(f"{session['role']}_dashboard"))

@app.route('/delete_todo/<int:todo_id>')
def delete_todo(todo_id):
    """Delete todo item"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM todos WHERE id = %s AND user_id = %s', (todo_id, session['user_id']))
            conn.commit()
            flash('Todo deleted successfully!')
        except Exception as e:
            flash('Error deleting todo')
        finally:
            cur.close()
            conn.close()
    else:
        flash('Database connection error')
    
    return redirect(url_for(f"{session['role']}_dashboard"))

# ===== MESSAGE ROUTES =====

@app.route('/admin/send_message', methods=['GET', 'POST'])
def admin_send_message():
    """Admin send message to employees"""
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            if request.method == 'POST':
                receiver_id = request.form['receiver_id']
                subject = request.form['subject']
                message = request.form['message']
                
                document_path = None
                document_filename = None
                
                # Handle file upload
                if 'document' in request.files:
                    file = request.files['document']
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        # Create unique filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"{timestamp}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(file_path)
                        document_path = file_path
                        document_filename = filename
                        flash(f'Document "{filename}" uploaded successfully!')
                    elif file and file.filename != '':
                        flash('File type not allowed. Please upload: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx')
                
                if receiver_id == 'all':
                    # Send to all employees
                    cur.execute('SELECT id FROM users WHERE role = %s', ('employee',))
                    employees = cur.fetchall()
                    for employee in employees:
                        cur.execute('''
                            INSERT INTO messages (sender_id, receiver_id, subject, message, document_path, document_filename) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (session['user_id'], employee[0], subject, message, document_path, document_filename))
                else:
                    cur.execute('''
                        INSERT INTO messages (sender_id, receiver_id, subject, message, document_path, document_filename) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (session['user_id'], receiver_id, subject, message, document_path, document_filename))
                
                conn.commit()
                flash('Message sent successfully!')
                return redirect(url_for('admin_dashboard'))
            
            # Get employees for dropdown
            cur.execute('SELECT id, name, email FROM users WHERE role = %s', ('employee',))
            employees = cur.fetchall()
            cur.close()
            conn.close()
            
            return render_template('admin/send_message.html', employees=employees)
            
        except Exception as e:
            flash('Error sending message')
    else:
        flash('Database connection error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/employee/send_message', methods=['GET', 'POST'])
def employee_send_message():
    """Employee send message to admin or other employees"""
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('employee_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            if request.method == 'POST':
                receiver_id = request.form['receiver_id']
                subject = request.form['subject']
                message = request.form['message']
                
                document_path = None
                document_filename = None
                
                # Handle file upload
                if 'document' in request.files:
                    file = request.files['document']
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        # Create unique filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"{timestamp}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(file_path)
                        document_path = file_path
                        document_filename = filename
                        flash(f'Document "{filename}" uploaded successfully!')
                    elif file and file.filename != '':
                        flash('File type not allowed. Please upload: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx')
                
                cur.execute('''
                    INSERT INTO messages (sender_id, receiver_id, subject, message, document_path, document_filename) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (session['user_id'], receiver_id, subject, message, document_path, document_filename))
                
                conn.commit()
                flash('Message sent successfully!')
                return redirect(url_for('employee_dashboard'))
            
            # Get recipients (admin and other employees)
            cur.execute('SELECT id, name, role FROM users WHERE id != %s', (session['user_id'],))
            recipients = cur.fetchall()
            cur.close()
            conn.close()
            
            return render_template('employee/send_message.html', recipients=recipients)
            
        except Exception as e:
            flash('Error sending message')
    else:
        flash('Database connection error')
    
    return redirect(url_for('employee_dashboard'))

@app.route('/inbox')
def inbox():
    """View received messages"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
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
            
        except Exception as e:
            flash('Error loading messages')
    else:
        flash('Database connection error')
    
    return redirect(url_for(f"{session['role']}_dashboard"))

@app.route('/download_document/<int:message_id>')
def download_document(message_id):
    """Download attached document"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT document_path, document_filename FROM messages WHERE id = %s', (message_id,))
            message = cur.fetchone()
            
            if message and message[0] and message[1]:
                document_path = message[0]
                document_filename = message[1]
                
                if os.path.exists(document_path):
                    return send_file(document_path, as_attachment=True, download_name=document_filename)
                else:
                    flash('Document file not found')
            else:
                flash('No document attached to this message')
            
            cur.close()
            conn.close()
        except Exception as e:
            flash('Error downloading document')
    else:
        flash('Database connection error')
    
    return redirect(url_for('inbox'))

# ===== PROFILE ROUTES =====

@app.route('/profile')
def profile():
    """View user profile"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE id = %s', (session['user_id'],))
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            template = f"{session['role']}/profile.html"
            return render_template(template, user=user)
            
        except Exception as e:
            flash('Error loading profile')
    else:
        flash('Database connection error')
    
    return redirect(url_for(f"{session['role']}_dashboard"))

# ===== EMPLOYEE MANAGEMENT ROUTES (ADMIN ONLY) =====

@app.route('/admin/add_employee', methods=['GET', 'POST'])
def add_employee():
    """Add new employee (Admin only)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('''
                    INSERT INTO users (employee_id, name, email, password, role) 
                    VALUES (%s, %s, %s, %s, 'employee')
                ''', (employee_id, name, email, password))
                conn.commit()
                flash('Employee added successfully!')
                return redirect(url_for('manage_employees'))
            except Exception as e:
                flash('Employee ID or email already exists')
            finally:
                cur.close()
                conn.close()
    
    return render_template('admin/add_employee.html')

@app.route('/admin/manage_employees')
def manage_employees():
    """Manage employees (Admin only)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, employee_id, name, email, created_at FROM users WHERE role = %s ORDER BY created_at DESC', ('employee',))
            employees = cur.fetchall()
            cur.close()
            conn.close()
            
            return render_template('admin/manage_employees.html', employees=employees)
        except Exception as e:
            flash('Error loading employees')
    else:
        flash('Database connection error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_employee/<int:employee_id>')
def delete_employee(employee_id):
    """Delete employee (Admin only)"""
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM users WHERE id = %s AND role = %s', (employee_id, 'employee'))
            conn.commit()
            flash('Employee deleted successfully!')
        except Exception as e:
            flash('Error deleting employee')
        finally:
            cur.close()
            conn.close()
    
    return redirect(url_for('manage_employees'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)