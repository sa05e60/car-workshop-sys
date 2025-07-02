from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
from flask_jwt_extended import JWTManager
import os
import re
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Use environment variables for secrets, fallback to defaults for development
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', '2981b42de8addb76b35e1e22e8874d52b7db9aaf9b55634f2745ee7d196cccf8b3e13ca08d4036361a09f4c04b2b938b7315be4c5a661748886212788f386f8f551645bf2a3254c2e560d2379bd22ae6e0156261c01c2b1743b54b5456e0a3f847533701f50d0e72ad3fe6c52bfcb2f65552ed4bd04ff7c700e89ceaa62b40275030112dc7a8d4da3f6ac4cea7017f39e5032a9017620aaa89623ac3c3294a9cd384e68000039a7d25680e07a0fdb14f703fca76e852ffb4bab5c920bcb69f1f2e2e37278845cbb557eaf24c7f1f497987747d75729e939e85bf6906396216c87d4803aedf0e5c204ea8cccd2b48de19c968c495375a7ae1b23aaec75c0085cf')

jwt = JWTManager(app)

# Database configuration
DATABASE = 'workshop.db'

def get_db_connection():
    """Create and return a database connection with error handling"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def close_db_connection(conn):
    """Safely close database connection"""
    if conn:
        try:
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('⚠️ Access Denied: This page requires administrator privileges. Please contact your system administrator if you need access.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def validate_phone(phone):
    """Validate phone number format"""
    phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]{10,}$')
    return bool(phone_pattern.match(phone))

def validate_email(email):
    """Validate email format"""
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))

def validate_year(year):
    """Validate year (must be reasonable for a car)"""
    try:
        year_int = int(year)
        return 1900 <= year_int <= datetime.now().year + 1
    except (ValueError, TypeError):
        return False

def validate_cost(cost):
    """Validate cost (must be positive number)"""
    try:
        cost_float = float(cost)
        return cost_float > 0
    except (ValueError, TypeError):
        return False

def init_db():
    """Initialize database with improved schema and error handling"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database during initialization")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Check if database needs migration
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Create or migrate users table
        if not existing_columns:
            # Create new table
            cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
                email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
            ''')
            logger.info("Created new users table")
        else:
            # Migrate existing table
            if 'email' not in existing_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
            if 'created_at' not in existing_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN created_at TEXT')
                # Update existing records with current timestamp
                cursor.execute("UPDATE users SET created_at = datetime('now') WHERE created_at IS NULL")
            if 'last_login' not in existing_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN last_login TEXT')
            logger.info("Migrated existing users table")

        # Check and migrate customers table
        cursor.execute("PRAGMA table_info(customers)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        if not existing_columns:
            cursor.execute('''
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                address TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            logger.info("Created new customers table")
        else:
            if 'email' not in existing_columns:
                cursor.execute('ALTER TABLE customers ADD COLUMN email TEXT')
            if 'address' not in existing_columns:
                cursor.execute('ALTER TABLE customers ADD COLUMN address TEXT')
            if 'updated_at' not in existing_columns:
                cursor.execute('ALTER TABLE customers ADD COLUMN updated_at TEXT')
                # Update existing records with current timestamp
                cursor.execute('UPDATE customers SET updated_at = created_at WHERE updated_at IS NULL')
            logger.info("Migrated existing customers table")

        # Check and migrate cars table
        cursor.execute("PRAGMA table_info(cars)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        if not existing_columns:
            cursor.execute('''
            CREATE TABLE cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                engine_type TEXT NOT NULL,
                customer_id INTEGER NOT NULL,
                license_plate TEXT,
                vin TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
            )
            ''')
            logger.info("Created new cars table")
        else:
            if 'license_plate' not in existing_columns:
                cursor.execute('ALTER TABLE cars ADD COLUMN license_plate TEXT')
            if 'vin' not in existing_columns:
                cursor.execute('ALTER TABLE cars ADD COLUMN vin TEXT')
            if 'updated_at' not in existing_columns:
                cursor.execute('ALTER TABLE cars ADD COLUMN updated_at TEXT')
                # Update existing records with current timestamp
                cursor.execute('UPDATE cars SET updated_at = created_at WHERE updated_at IS NULL')
            logger.info("Migrated existing cars table")

        # Check and migrate services table
        cursor.execute("PRAGMA table_info(services)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        if not existing_columns:
            cursor.execute('''
            CREATE TABLE services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                cost REAL NOT NULL CHECK (cost > 0),
                status TEXT NOT NULL CHECK (status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')),
                car_id INTEGER NOT NULL,
                description TEXT,
                start_date TEXT DEFAULT CURRENT_TIMESTAMP,
                end_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (car_id) REFERENCES cars (id) ON DELETE CASCADE
            )
            ''')
            logger.info("Created new services table")
        else:
            if 'description' not in existing_columns:
                cursor.execute('ALTER TABLE services ADD COLUMN description TEXT')
            if 'start_date' not in existing_columns:
                cursor.execute('ALTER TABLE services ADD COLUMN start_date TEXT')
                # Update existing records with current timestamp
                cursor.execute('UPDATE services SET start_date = created_at WHERE start_date IS NULL')
            if 'end_date' not in existing_columns:
                cursor.execute('ALTER TABLE services ADD COLUMN end_date TEXT')
            if 'updated_at' not in existing_columns:
                cursor.execute('ALTER TABLE services ADD COLUMN updated_at TEXT')
                # Update existing records with current timestamp
                cursor.execute('UPDATE services SET updated_at = created_at WHERE updated_at IS NULL')
            logger.info("Migrated existing services table")

        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cars_customer_id ON cars(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_services_car_id ON services(car_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_services_status ON services(status)')
        
        conn.commit()
        logger.info("Database initialized and migrated successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn)


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Input validation
        if not username or not password:
            flash('Please enter both username and password.')
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash('System error. Please try again later.')
            return render_template('login.html')

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, password, role, username 
                FROM users 
                WHERE username = ?
            """, (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                # Update last login time
                cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user['id'],))
                conn.commit()

                # Set session data
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['login_time'] = datetime.now().isoformat()

                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('dashboard'))
            else:
                logger.warning(f"Failed login attempt for username: {username}")
                flash('Invalid username or password.')
        except sqlite3.Error as e:
            logger.error(f"Database error during login: {e}")
            flash('System error. Please try again later.')
        finally:
            close_db_connection(conn)

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session['username'], role=session['role'])

@app.route('/logout')
def logout():
    if 'username' in session:
        logger.info(f"User {session['username']} logged out")
    session.clear()
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

@app.route('/customers', methods=['GET', 'POST'])
@login_required
def manage_customers():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return render_template('customers.html', customers=[])

    try:
        cursor = conn.cursor()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            address = request.form.get('address', '').strip()

            # Input validation
            if not name:
                flash('Customer name is required.')
            elif not phone:
                flash('Phone number is required.')
            elif not validate_phone(phone):
                flash('Please enter a valid phone number.')
            elif email and not validate_email(email):
                flash('Please enter a valid email address.')
            else:
                try:
                    cursor.execute("""
                        INSERT INTO customers (name, phone, email, address, created_at, updated_at) 
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (name, phone, email, address))
                    conn.commit()
                    flash('Customer added successfully!')
                    logger.info(f"New customer added: {name}")
                except sqlite3.IntegrityError:
                    flash('A customer with this phone number already exists.')
                except sqlite3.Error as e:
                    logger.error(f"Database error adding customer: {e}")
                    flash('Error adding customer. Please try again.')

        # Get all customers with better formatting
        cursor.execute("""
            SELECT id, name, phone, email, address, created_at, updated_at 
            FROM customers 
            ORDER BY created_at DESC
        """)
        customers = cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Database error in customers: {e}")
        flash('Database error. Please try again.')
        customers = []
    finally:
        close_db_connection(conn)

    return render_template('customers.html', customers=customers)

@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
@admin_required
def delete_customer(customer_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return redirect(url_for('manage_customers'))

    try:
        cursor = conn.cursor()
        
        # Check if customer exists
        cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            flash('Customer not found.')
        else:
            # Check if customer has cars
            cursor.execute("SELECT COUNT(*) FROM cars WHERE customer_id = ?", (customer_id,))
            car_count = cursor.fetchone()[0]
            
            if car_count > 0:
                flash(f"Cannot delete customer '{customer['name']}' - they have {car_count} car(s) registered.")
            else:
                cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
                conn.commit()
                flash(f"Customer '{customer['name']}' has been deleted successfully.")
                logger.info(f"Customer {customer_id} deleted by admin {session['username']}")
    except sqlite3.Error as e:
        logger.error(f"Database error deleting customer: {e}")
        flash('Error deleting customer. Please try again.')
    finally:
        close_db_connection(conn)

    return redirect(url_for('manage_customers'))


@app.route('/cars', methods=['GET', 'POST'])
@login_required
def manage_cars():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return render_template('cars.html', cars=[], customers=[])

    try:
        cursor = conn.cursor()

        # Get customer list for dropdown
        cursor.execute("SELECT id, name, phone FROM customers ORDER BY name")
        customer_list = cursor.fetchall()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            model = request.form.get('model', '').strip()
            year = request.form.get('year', '').strip()
            engine_type = request.form.get('engine_type', '').strip()
            customer_id = request.form.get('customer_id', '').strip()
            license_plate = request.form.get('license_plate', '').strip()
            vin = request.form.get('vin', '').strip()

            # Input validation
            if not all([name, model, year, engine_type, customer_id]):
                flash('Please fill in all required fields.')
            elif not validate_year(year):
                flash('Please enter a valid year.')
            else:
                try:
                    cursor.execute("""
                        INSERT INTO cars (name, model, year, engine_type, customer_id, license_plate, vin, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (name, model, year, engine_type, customer_id, license_plate, vin))
                    conn.commit()
                    flash('Car added successfully!')
                    logger.info(f"New car added: {name} {model}")
                except sqlite3.IntegrityError:
                    flash('Error: This car may already exist.')
                except sqlite3.Error as e:
                    logger.error(f"Database error adding car: {e}")
                    flash('Error adding car. Please try again.')

        # Get all cars with customer information
        cursor.execute("""
            SELECT c.id, c.name, c.model, c.year, c.engine_type, c.license_plate, c.vin, 
                   c.created_at, c.updated_at, cu.name as customer_name, cu.phone as customer_phone
            FROM cars c
            JOIN customers cu ON c.customer_id = cu.id
            ORDER BY c.created_at DESC
        """)
        cars = cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Database error in cars: {e}")
        flash('Database error. Please try again.')
        cars = []
        customer_list = []
    finally:
        close_db_connection(conn)

    return render_template('cars.html', cars=cars, customers=customer_list)

@app.route('/delete_car/<int:car_id>', methods=['POST'])
@admin_required
def delete_car(car_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return redirect(url_for('manage_cars'))

    try:
        cursor = conn.cursor()
        
        # Check if car exists
        cursor.execute("SELECT name, model FROM cars WHERE id = ?", (car_id,))
        car = cursor.fetchone()
        
        if not car:
            flash('Car not found.')
        else:
            # Check if car has services
            cursor.execute("SELECT COUNT(*) FROM services WHERE car_id = ?", (car_id,))
            service_count = cursor.fetchone()[0]
            
            if service_count > 0:
                flash(f"Cannot delete car '{car['name']} {car['model']}' - it has {service_count} service(s) registered.")
            else:
                cursor.execute("DELETE FROM cars WHERE id = ?", (car_id,))
                conn.commit()
                flash(f"Car '{car['name']} {car['model']}' has been deleted successfully.")
                logger.info(f"Car {car_id} deleted by admin {session['username']}")
    except sqlite3.Error as e:
        logger.error(f"Database error deleting car: {e}")
        flash('Error deleting car. Please try again.')
    finally:
        close_db_connection(conn)

    return redirect(url_for('manage_cars'))

@app.route('/services', methods=['GET', 'POST'])
@login_required
def manage_services():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return render_template('services.html', services=[], cars=[], role=session.get('role'))

    try:
        cursor = conn.cursor()

        # Get car list for dropdown with customer information
        cursor.execute("""
            SELECT c.id, c.name, c.model, c.year, cu.name as customer_name
            FROM cars c
            JOIN customers cu ON c.customer_id = cu.id
            ORDER BY c.name, c.model
        """)
        car_list = cursor.fetchall()

        if request.method == 'POST':
            service_type = request.form.get('type', '').strip()
            cost = request.form.get('cost', '').strip()
            status = request.form.get('status', 'Pending').strip()
            car_id = request.form.get('car_id', '').strip()
            description = request.form.get('description', '').strip()

            # Input validation
            if not all([service_type, cost, car_id]):
                flash('Please fill in all required fields.')
            elif not validate_cost(cost):
                flash('Please enter a valid cost (must be greater than 0).')
            elif status not in ['Pending', 'In Progress', 'Completed', 'Cancelled']:
                flash('Please select a valid status.')
            else:
                try:
                    cursor.execute("""
                        INSERT INTO services (type, cost, status, car_id, description, start_date, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (service_type, cost, status, car_id, description))
                    conn.commit()
                    flash('Service added successfully!')
                    logger.info(f"New service added: {service_type} for car {car_id}")
                except sqlite3.IntegrityError:
                    flash('Error: Invalid car selection.')
                except sqlite3.Error as e:
                    logger.error(f"Database error adding service: {e}")
                    flash('Error adding service. Please try again.')

        # Get services with car and customer information
        role = session.get('role')
        
        # Build the base query
        base_query = """
            SELECT s.id, s.type, s.cost, s.status, s.description, s.start_date, s.end_date,
                   s.created_at, s.updated_at, c.name as car_name, c.model as car_model,
                   cu.name as customer_name, cu.phone as customer_phone
            FROM services s
            JOIN cars c ON s.car_id = c.id
            JOIN customers cu ON c.customer_id = cu.id
        """
        
        # Add WHERE conditions for filtering
        where_conditions = []
        params = []
        
        # Status filter for non-admin users
        if role != 'admin':
            where_conditions.append("s.status != 'Cancelled'")
        
        # Search filter
        search_term = request.args.get('search', '').strip()
        if search_term:
            where_conditions.append("(s.type LIKE ? OR s.description LIKE ?)")
            params.extend([f'%{search_term}%', f'%{search_term}%'])
        
        # Status filter
        status_filter = request.args.get('status_filter', '').strip()
        if status_filter:
            where_conditions.append("s.status = ?")
            params.append(status_filter)
        
        # Customer filter
        customer_filter = request.args.get('customer_filter', '').strip()
        if customer_filter:
            where_conditions.append("cu.name = ?")
            params.append(customer_filter)
        
        # Build final query
        if where_conditions:
            query = base_query + " WHERE " + " AND ".join(where_conditions) + " ORDER BY s.created_at DESC"
        else:
            query = base_query + " ORDER BY s.created_at DESC"
        
        cursor.execute(query, params)
        services = cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Database error in services: {e}")
        flash('Database error. Please try again.')
        services = []
        car_list = []
    finally:
        close_db_connection(conn)

    return render_template('services.html', services=services, cars=car_list, role=role)

@app.route('/end_service/<int:service_id>', methods=['POST'])
@login_required
def end_service(service_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return redirect(url_for('manage_services'))

    try:
        cursor = conn.cursor()
        
        # Check if service exists and get current status
        cursor.execute("SELECT status, type FROM services WHERE id = ?", (service_id,))
        service = cursor.fetchone()
        
        if not service:
            flash('Service not found.')
        elif service['status'] == 'Completed':
            flash('Service is already completed.')
        elif service['status'] == 'Cancelled':
            flash('Cannot complete a cancelled service.')
        else:
            cursor.execute("""
                UPDATE services 
                SET status = 'Completed', end_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (service_id,))
            conn.commit()
            flash(f"Service '{service['type']}' completed successfully!")
            logger.info(f"Service {service_id} completed by user {session['username']}")
    except sqlite3.Error as e:
        logger.error(f"Database error ending service: {e}")
        flash('Error completing service. Please try again.')
    finally:
        close_db_connection(conn)

    return redirect(url_for('manage_services'))

@app.route('/start_service/<int:service_id>', methods=['POST'])
@login_required
def start_service(service_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return redirect(url_for('manage_services'))

    try:
        cursor = conn.cursor()
        
        # Check if service exists and get current status
        cursor.execute("SELECT status, type FROM services WHERE id = ?", (service_id,))
        service = cursor.fetchone()
        
        if not service:
            flash('Service not found.')
        elif service['status'] != 'Pending':
            flash(f"Service is already {service['status'].lower()}.")
        else:
            cursor.execute("""
                UPDATE services 
                SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (service_id,))
            conn.commit()
            flash(f"Service '{service['type']}' started successfully!")
            logger.info(f"Service {service_id} started by user {session['username']}")
    except sqlite3.Error as e:
        logger.error(f"Database error starting service: {e}")
        flash('Error starting service. Please try again.')
    finally:
        close_db_connection(conn)

    return redirect(url_for('manage_services'))

@app.route('/delete_service/<int:service_id>', methods=['POST'])
@admin_required
def delete_service(service_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return redirect(url_for('manage_services'))

    try:
        cursor = conn.cursor()
        
        # Check if service exists
        cursor.execute("SELECT type FROM services WHERE id = ?", (service_id,))
        service = cursor.fetchone()
        
        if not service:
            flash('Service not found.')
        else:
            cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
            conn.commit()
            flash(f"Service '{service['type']}' has been deleted successfully.")
            logger.info(f"Service {service_id} deleted by admin {session['username']}")
    except sqlite3.Error as e:
        logger.error(f"Database error deleting service: {e}")
        flash('Error deleting service. Please try again.')
    finally:
        close_db_connection(conn)

    return redirect(url_for('manage_services'))


@app.route('/report')
@admin_required
def report():
    conn = get_db_connection()
    if not conn:
        flash('Database connection error. Please try again.')
        return render_template('report.html', report=[], summary={})

    try:
        cursor = conn.cursor()
        
        # Get detailed report data
        cursor.execute("""
            SELECT s.type, s.cost, s.status, s.start_date, s.end_date, s.created_at,
                   c.name as car_name, c.model as car_model, c.year as car_year,
                   cu.name as customer_name, cu.phone as customer_phone
            FROM services s 
            JOIN cars c ON s.car_id = c.id
            JOIN customers cu ON c.customer_id = cu.id
            ORDER BY s.created_at DESC
        """)
        report_data = cursor.fetchall()

        # Get summary statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_services,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_services,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending_services,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_services,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled_services,
                SUM(cost) as total_revenue,
                AVG(cost) as avg_service_cost
            FROM services
        """)
        summary = cursor.fetchone()

    except sqlite3.Error as e:
        logger.error(f"Database error in report: {e}")
        flash('Database error. Please try again.')
        report_data = []
        summary = {}
    finally:
        close_db_connection(conn)

    return render_template('report.html', report=report_data, summary=summary)


def add_admin_user():
    """Add admin user with improved error handling"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for admin user creation")
        return False

    try:
        cursor = conn.cursor()
        username = "admin"
        password = "2079" 
        hashed_password = generate_password_hash(password)

        # Check if created_at column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'created_at' in columns:
            cursor.execute("""
                INSERT INTO users (username, password, role, created_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (username, hashed_password, 'admin'))
        else:
            cursor.execute("""
                INSERT INTO users (username, password, role) 
                VALUES (?, ?, ?)
            """, (username, hashed_password, 'admin'))
            
        conn.commit()
        logger.info(f"Admin user '{username}' created successfully")
        return True
    except sqlite3.IntegrityError:
        logger.info(f"Admin user '{username}' already exists")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error creating admin user: {e}")
        return False
    finally:
        close_db_connection(conn)

def add_employee_user():
    """Add employee user with improved error handling"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for employee user creation")
        return False

    try:
        cursor = conn.cursor()
        username = "sa05_e60"
        password = "saif2079"
        hashed_password = generate_password_hash(password)

        # Check if created_at column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'created_at' in columns:
            cursor.execute("""
                INSERT INTO users (username, password, role, created_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (username, hashed_password, 'user'))
        else:
            cursor.execute("""
                INSERT INTO users (username, password, role) 
                VALUES (?, ?, ?)
            """, (username, hashed_password, 'user'))
            
        conn.commit()
        logger.info(f"Employee user '{username}' created successfully")
        return True
    except sqlite3.IntegrityError:
        logger.info(f"Employee user '{username}' already exists")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error creating employee user: {e}")
        return False
    finally:
        close_db_connection(conn)




if __name__ == '__main__':
    # Initialize database
    if not init_db():
        logger.error("Failed to initialize database. Exiting.")
        exit(1)
    
    # Create default users
    if not add_admin_user():
        logger.error("Failed to create admin user.")
    
    if not add_employee_user():
        logger.error("Failed to create employee user.")
    
    # Get configuration from environment variables
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting workshop management system on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

