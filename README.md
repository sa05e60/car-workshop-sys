<<<<<<< HEAD
# Workshop Management System

A comprehensive Flask-based web application for managing automotive workshop operations including customers, cars, and services.

## Developer

**Created by:** Saif Fadhil  
**Date:** 2025  
**Technology Stack:** Python, Flask, SQLite, HTML/CSS, JavaScript, Bootstrap

---

This project demonstrates modern web development practices, security implementation, and business logic for automotive workshop management. Built with industry-standard security measures and responsive design principles.

## Features

- **User Authentication**: Secure login system with role-based access control
- **Customer Management**: Add and manage customer information
- **Car Management**: Track customer vehicles with detailed information
- **Service Management**: Create and track service requests with status updates
- **Reporting**: Comprehensive reports for administrators
- **Responsive Design**: Modern UI with Bootstrap and custom styling

## Security Improvements

- Environment variable support for sensitive configuration
- Input validation and sanitization
- SQL injection prevention with parameterized queries
- Session management with proper security settings
- Role-based access control
- Comprehensive error handling and logging

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd workshop-management-system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional)
   ```bash
   # Create a .env file
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

## Default Users

The system creates two default users on first run:

- **Admin User**:
  - Username: `abdullah`
  - Password: `19971997`
  - Role: `admin`

- **Employee User**:
  - Username: `saif_user`
  - Password: `saif2079`
  - Role: `user`

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password`: Hashed password
- `role`: User role (admin/user)
- `email`: User email (optional)
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp

### Customers Table
- `id`: Primary key
- `name`: Customer name
- `phone`: Phone number
- `email`: Email address (optional)
- `address`: Address (optional)
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

### Cars Table
- `id`: Primary key
- `name`: Car name/brand
- `model`: Car model
- `year`: Manufacturing year
- `engine_type`: Engine type
- `customer_id`: Foreign key to customers
- `license_plate`: License plate number (optional)
- `vin`: Vehicle identification number (optional)
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

### Services Table
- `id`: Primary key
- `type`: Service type
- `cost`: Service cost
- `status`: Service status (Pending/In Progress/Completed/Cancelled)
- `car_id`: Foreign key to cars
- `description`: Service description (optional)
- `start_date`: Service start date
- `end_date`: Service completion date (optional)
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

## API Endpoints

- `GET /` - Redirects to login
- `GET/POST /login` - User authentication
- `GET /dashboard` - Main dashboard (requires login)
- `GET /logout` - User logout
- `GET/POST /customers` - Customer management (requires login)
- `GET/POST /cars` - Car management (requires login)
- `GET/POST /services` - Service management (requires login)
- `POST /end_service/<id>` - Complete a service (requires login)
- `POST /delete_service/<id>` - Delete a service (requires admin)
- `GET /report` - Service reports (requires admin)

## Configuration

The application supports different environments through the `config.py` file:

- **Development**: Debug mode enabled, detailed logging
- **Production**: Security-focused settings, minimal logging
- **Testing**: Test database, CSRF disabled

Set the `FLASK_ENV` environment variable to switch between configurations.

## Security Features

- **Password Hashing**: All passwords are hashed using Werkzeug's security functions
- **Session Management**: Secure session handling with configurable timeouts
- **Input Validation**: Comprehensive validation for all user inputs
- **SQL Injection Prevention**: Parameterized queries throughout the application
- **Access Control**: Role-based permissions for different operations
- **Error Handling**: Graceful error handling without exposing sensitive information

## Logging

The application includes comprehensive logging for:
- User authentication events
- Database operations
- Error tracking
- Security events

Logs are written to the console and can be configured through environment variables.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository. 
=======
# car-workshop-sys
>>>>>>> 6ea824dcdf92325c77199df3fe72e1636bf4bd68
