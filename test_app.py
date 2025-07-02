import unittest
import tempfile
import os
import sqlite3
from app import app, init_db, get_db_connection, validate_phone, validate_email, validate_year, validate_cost

class WorkshopManagementTestCase(unittest.TestCase):
    """Test cases for the Workshop Management System"""

    def setUp(self):
        """Set up test environment before each test"""
        # Create a temporary database for testing
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        
        # Initialize test database
        with app.app_context():
            init_db()

    def tearDown(self):
        """Clean up after each test"""
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_home_page_redirect(self):
        """Test that home page redirects to login"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn(b'login', response.location.lower())

    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.app.get('/dashboard', follow_redirects=True)
        self.assertIn(b'login', response.data)

    def test_validation_functions(self):
        """Test input validation functions"""
        # Phone validation
        self.assertTrue(validate_phone('+1234567890'))
        self.assertTrue(validate_phone('123-456-7890'))
        self.assertTrue(validate_phone('(123) 456-7890'))
        self.assertFalse(validate_phone('123'))
        self.assertFalse(validate_phone('abc'))

        # Email validation
        self.assertTrue(validate_email('test@example.com'))
        self.assertTrue(validate_email('user.name@domain.co.uk'))
        self.assertFalse(validate_email('invalid-email'))
        self.assertFalse(validate_email('@domain.com'))

        # Year validation
        self.assertTrue(validate_year('2020'))
        self.assertTrue(validate_year('1990'))
        self.assertFalse(validate_year('1800'))
        self.assertFalse(validate_year('2030'))
        self.assertFalse(validate_year('abc'))

        # Cost validation
        self.assertTrue(validate_cost('100.50'))
        self.assertTrue(validate_cost('0.01'))
        self.assertFalse(validate_cost('0'))
        self.assertFalse(validate_cost('-10'))
        self.assertFalse(validate_cost('abc'))

    def test_database_connection(self):
        """Test database connection function"""
        with app.app_context():
            conn = get_db_connection()
            self.assertIsNotNone(conn)
            self.assertIsInstance(conn, sqlite3.Connection)
            conn.close()

    def test_customers_page_requires_login(self):
        """Test that customers page requires authentication"""
        response = self.app.get('/customers', follow_redirects=True)
        self.assertIn(b'login', response.data)

    def test_cars_page_requires_login(self):
        """Test that cars page requires authentication"""
        response = self.app.get('/cars', follow_redirects=True)
        self.assertIn(b'login', response.data)

    def test_services_page_requires_login(self):
        """Test that services page requires authentication"""
        response = self.app.get('/services', follow_redirects=True)
        self.assertIn(b'login', response.data)

    def test_report_page_requires_admin(self):
        """Test that report page requires admin access"""
        response = self.app.get('/report', follow_redirects=True)
        self.assertIn(b'login', response.data)

if __name__ == '__main__':
    unittest.main() 