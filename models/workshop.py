# models/workshop.py
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

def init_db():
    with sqlite3.connect('workshop.db') as conn:
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'user')) NOT NULL
        )''')

        c.execute("SELECT * FROM users WHERE username = ?", ('admin',))
        if not c.fetchone():
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (
                'admin',
                generate_password_hash('admin123'),
                'admin'
            ))

        c.execute('''CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            model TEXT,
            year INTEGER,
            engine_type TEXT,
            customer_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            cost REAL,
            status TEXT,
            car_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (car_id) REFERENCES cars(id)
        )''')

def create_customer(name, phone):
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect('workshop.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO customers (name, phone, created_at) VALUES (?, ?, ?)", (name, phone, created_at))

def create_car(name, model, year, engine_type, customer_id):
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect('workshop.db') as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO cars (name, model, year, engine_type, customer_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, model, year, engine_type, customer_id, created_at))

def create_service(type, cost, status, car_id):
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect('workshop.db') as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO services (type, cost, status, car_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (type, cost, status, car_id, created_at))

def get_all_customers():
    with sqlite3.connect('workshop.db') as conn:
        c = conn.cursor()
        return c.execute("SELECT * FROM customers").fetchall()

def get_all_cars():
    with sqlite3.connect('workshop.db') as conn:
        c = conn.cursor()
        return c.execute("SELECT * FROM cars").fetchall()
