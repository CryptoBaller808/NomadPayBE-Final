# NomadPay Backend API

Production-ready Flask backend for NomadPay with fixed authentication system.

## 🚀 **Deployment Structure**

This backend uses a **root-level structure** optimized for Render deployment:

```
nomadpay-backend-final/
├── app.py                 # Main Flask application (entry point)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment variables template
└── .gitignore            # Git ignore rules
```

## 🔧 **Render Deployment Configuration**

### **Build Command**
```bash
pip install -r requirements.txt
```

### **Start Command** ✅
```bash
gunicorn app:app
```

**Important**: Use `gunicorn app:app` NOT `gunicorn src.main:app`

## 🌟 **Key Features**

### **✅ Fixed Authentication System**
- Returns `access_token` and `refresh_token` (not just `token`)
- Proper JWT token generation and validation
- Secure password hashing with Werkzeug
- Complete user registration and login flows

### **✅ Production-Ready Endpoints**
- **Health Check**: `/health` (confirmed working)
- **Authentication**: `/api/auth/*` (register, login, refresh, logout)
- **Wallet Management**: `/api/wallet/*` (balances, history)
- **Transactions**: `/api/transactions/*` (send, history)
- **QR Codes**: `/api/qr/*` (generate, scan)
- **Admin Panel**: `/api/admin/*` (users, transactions, analytics)

### **✅ Database Integration**
- SQLite database with automatic initialization
- User and wallet table creation
- Default wallet setup for new users
- Proper foreign key relationships

### **✅ Security Features**
- CORS configuration for production domains
- JWT token expiry (1 hour access, 7 days refresh)
- Password strength validation
- Input sanitization and validation
- Comprehensive error handling

## 🔐 **Environment Variables**

Create these environment variables in Render:

```bash
SECRET_KEY=your-super-secret-jwt-key-here
DATABASE_URL=nomadpay.db
FLASK_ENV=production
PORT=5000
```

## 🎯 **API Response Format**

### **Registration/Login Response (FIXED)**
```json
{
  "success": true,
  "message": "Registration successful",
  "access_token": "eyJ...",    # ✅ Correct field name
  "refresh_token": "eyJ...",   # ✅ Added refresh token
  "user": {
    "id": "1",
    "email": "user@nomadpay.io",
    "role": "user",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### **Health Check Response**
```json
{
  "service": "NomadPay Backend API",
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00"
}
```

## 🌍 **CORS Configuration**

Configured for these domains:
- `https://nomadpay-frontend.onrender.com`
- `https://nomadpayadmin.onrender.com`
- `http://localhost:3000` (development)
- `http://localhost:3001` (development)

## 📋 **Deployment Checklist**

1. ✅ Upload all files to GitHub repository root
2. ✅ Set build command: `pip install -r requirements.txt`
3. ✅ Set start command: `gunicorn app:app`
4. ✅ Configure environment variables
5. ✅ Deploy and test `/health` endpoint
6. ✅ Test authentication endpoints

## 🎉 **Expected Results**

After successful deployment:
- ✅ Health endpoint: `https://your-app.onrender.com/health`
- ✅ Registration returns `access_token` and `refresh_token`
- ✅ Login returns `access_token` and `refresh_token`
- ✅ Frontend console shows: "Received access_token: true"
- ✅ Users can complete authentication flow successfully

## 🌺 **Aloha & Success!**

This backend is production-ready and will resolve all authentication issues once deployed with the correct `gunicorn app:app` command!

Mahalo nui loa! 🤙

