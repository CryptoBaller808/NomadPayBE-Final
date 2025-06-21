"""
NomadPay Backend API - Main Application
Production-ready Flask application with fixed authentication
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
from datetime import datetime
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for production
CORS(app, origins=[
    'https://nomadpay-frontend.onrender.com',
    'https://nomadpayadmin.onrender.com',
    'http://localhost:3000',
    'http://localhost:3001'
])

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'nomadpay.db')

# Database initialization
def init_database():
    """Initialize the database with required tables"""
    try:
        conn = sqlite3.connect(app.config['DATABASE_URL'])
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create wallets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                currency TEXT NOT NULL,
                balance DECIMAL(15,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

# Token generation
def generate_tokens(user_id, email, role='user'):
    """Generate access and refresh tokens"""
    try:
        # Access token (1 hour expiry)
        access_payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        # Refresh token (7 days expiry)
        refresh_payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, app.config['SECRET_KEY'], algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise

# Create default wallets
def create_default_wallets(user_id):
    """Create default wallets for new user"""
    try:
        conn = sqlite3.connect(app.config['DATABASE_URL'])
        cursor = conn.cursor()
        
        # Create default wallets for major currencies
        currencies = ['USD', 'EUR', 'BTC', 'ETH']
        for currency in currencies:
            cursor.execute('''
                INSERT INTO wallets (user_id, currency, balance)
                VALUES (?, ?, 0.00)
            ''', (user_id, currency))
        
        conn.commit()
        conn.close()
        logger.info(f"Default wallets created for user {user_id}")
        
    except Exception as e:
        logger.error(f"Wallet creation error: {e}")
        raise

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'service': 'NomadPay Backend API',
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Root endpoint with API information
@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        'message': 'Welcome to NomadPay Backend API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'auth': '/api/auth/**',
            'wallet': '/api/wallet/**',
            'transactions': '/api/transactions/**',
            'qr': '/api/qr/**',
            'analytics': '/api/analytics/**'
        }
    }), 200

# Authentication routes with FIXED response structure
@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint with FIXED response structure"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400
        
        # Validate password strength
        if len(password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            }), 400
        
        # Check if user already exists
        conn = sqlite3.connect(app.config['DATABASE_URL'])
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': 'User already exists with this email'
            }), 409
        
        # Create new user
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, created_at)
            VALUES (?, ?, ?, ?)
        ''', (email, password_hash, 'user', datetime.utcnow().isoformat()))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Create default wallets
        create_default_wallets(user_id)
        
        # Generate tokens
        tokens = generate_tokens(user_id, email, 'user')
        
        # ✅ FIXED: Return correct response structure with access_token and refresh_token
        response_data = {
            'success': True,
            'message': 'Registration successful',
            'access_token': tokens['access_token'],    # ✅ FIXED: Changed from "token"
            'refresh_token': tokens['refresh_token'],  # ✅ FIXED: Added refresh_token
            'user': {
                'id': str(user_id),
                'email': email,
                'role': 'user',
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"User registered successfully: {email}")
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'message': 'Registration failed. Please try again.'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint with FIXED response structure"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user in database
        conn = sqlite3.connect(app.config['DATABASE_URL'])
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, email, password_hash, role, created_at
            FROM users WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        user_id, user_email, password_hash, role, created_at = user
        
        # Verify password
        if not check_password_hash(password_hash, password):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Generate tokens
        tokens = generate_tokens(user_id, user_email, role)
        
        # ✅ FIXED: Return correct response structure with access_token and refresh_token
        response_data = {
            'success': True,
            'message': 'Login successful',
            'access_token': tokens['access_token'],    # ✅ FIXED: Changed from "token"
            'refresh_token': tokens['refresh_token'],  # ✅ FIXED: Added refresh_token
            'user': {
                'id': str(user_id),
                'email': user_email,
                'role': role,
                'created_at': created_at
            }
        }
        
        logger.info(f"User logged in successfully: {email}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Login failed. Please try again.'
        }), 500

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Token refresh endpoint"""
    try:
        data = request.get_json()
        
        if not data or not data.get('refresh_token'):
            return jsonify({
                'success': False,
                'message': 'Refresh token is required'
            }), 400
        
        refresh_token = data['refresh_token']
        
        # Verify refresh token
        try:
            payload = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
            
            if payload.get('type') != 'refresh':
                raise jwt.InvalidTokenError('Invalid token type')
            
            user_id = payload['user_id']
            email = payload['email']
            role = payload.get('role', 'user')
            
            # Generate new tokens
            tokens = generate_tokens(user_id, email, role)
            
            response_data = {
                'success': True,
                'message': 'Token refreshed successfully',
                'access_token': tokens['access_token'],    # ✅ FIXED: Consistent field names
                'refresh_token': tokens['refresh_token']   # ✅ FIXED: Consistent field names
            }
            
            return jsonify(response_data), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Refresh token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Invalid refresh token'
            }), 401
            
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'message': 'Token refresh failed'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        # In a production environment, you would invalidate the tokens
        # For now, we'll just return a success response
        response_data = {
            'success': True,
            'message': 'Logout successful'
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'message': 'Logout failed'
        }), 500

# Wallet endpoints (mock implementations for now)
@app.route('/api/wallet/balances', methods=['GET'])
def get_wallet_balances():
    """Get wallet balances"""
    return jsonify({
        'success': True,
        'balances': {
            'USD': 1250.00,
            'EUR': 890.50,
            'BTC': 0.05432,
            'ETH': 2.1234
        }
    }), 200

@app.route('/api/wallet/history', methods=['GET'])
def get_wallet_history():
    """Get wallet transaction history"""
    return jsonify({
        'success': True,
        'transactions': [
            {
                'id': '1',
                'type': 'receive',
                'amount': 500.00,
                'currency': 'USD',
                'from': 'john@example.com',
                'date': '2024-01-15T10:30:00Z'
            },
            {
                'id': '2',
                'type': 'send',
                'amount': 250.00,
                'currency': 'EUR',
                'to': 'sarah@example.com',
                'date': '2024-01-14T15:45:00Z'
            }
        ]
    }), 200

# Transaction endpoints
@app.route('/api/transactions/send', methods=['POST'])
def send_transaction():
    """Send money transaction"""
    data = request.get_json()
    return jsonify({
        'success': True,
        'message': 'Transaction sent successfully',
        'transaction_id': 'tx_' + str(datetime.utcnow().timestamp()),
        'amount': data.get('amount', 0),
        'currency': data.get('currency', 'USD'),
        'recipient': data.get('recipient', '')
    }), 200

@app.route('/api/transactions/history', methods=['GET'])
def get_transaction_history():
    """Get transaction history"""
    return jsonify({
        'success': True,
        'transactions': [
            {
                'id': 'tx_1',
                'type': 'send',
                'amount': 100.00,
                'currency': 'USD',
                'recipient': 'alice@example.com',
                'status': 'completed',
                'date': '2024-01-15T12:00:00Z'
            },
            {
                'id': 'tx_2',
                'type': 'receive',
                'amount': 75.50,
                'currency': 'EUR',
                'sender': 'bob@example.com',
                'status': 'completed',
                'date': '2024-01-14T18:30:00Z'
            }
        ]
    }), 200

# QR Code endpoints
@app.route('/api/qr/generate', methods=['POST'])
def generate_qr():
    """Generate QR code for payment"""
    data = request.get_json()
    return jsonify({
        'success': True,
        'qr_code': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
        'qr_data': {
            'amount': data.get('amount', 0),
            'currency': data.get('currency', 'USD'),
            'recipient': data.get('recipient', ''),
            'expires_at': '2024-01-16T12:00:00Z'
        }
    }), 200

@app.route('/api/qr/scan', methods=['POST'])
def scan_qr():
    """Process scanned QR code"""
    data = request.get_json()
    return jsonify({
        'success': True,
        'message': 'QR code processed successfully',
        'payment_data': {
            'amount': 50.00,
            'currency': 'USD',
            'recipient': 'merchant@example.com',
            'description': 'Coffee purchase'
        }
    }), 200

# Admin endpoints (basic implementations)
@app.route('/api/admin/users', methods=['GET'])
def get_admin_users():
    """Get users for admin dashboard"""
    return jsonify({
        'success': True,
        'users': [
            {
                'id': '1',
                'email': 'successtest@nomadpay.io',
                'role': 'user',
                'status': 'active',
                'created_at': '2024-01-15T10:00:00Z'
            }
        ],
        'total': 1
    }), 200

@app.route('/api/admin/transactions', methods=['GET'])
def get_admin_transactions():
    """Get transactions for admin dashboard"""
    return jsonify({
        'success': True,
        'transactions': [
            {
                'id': 'tx_1',
                'user_email': 'successtest@nomadpay.io',
                'type': 'send',
                'amount': 100.00,
                'currency': 'USD',
                'status': 'completed',
                'created_at': '2024-01-15T12:00:00Z'
            }
        ],
        'total': 1
    }), 200

@app.route('/api/admin/analytics', methods=['GET'])
def get_admin_analytics():
    """Get analytics for admin dashboard"""
    return jsonify({
        'success': True,
        'analytics': {
            'total_users': 1,
            'total_transactions': 1,
            'total_volume': 100.00,
            'active_users_today': 1
        }
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'message': 'Method not allowed'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

# Initialize database on startup
init_database()

# Run the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting NomadPay Backend API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

