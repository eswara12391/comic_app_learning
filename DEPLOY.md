# Deployment Guide - Comic Learning App

## Issues Fixed

### 1. ✅ Database Connection Error (MYSQL_CURSORCLASS)
**Problem**: `TypeError: getattr(): attribute name must be string`
**Solution**: Changed `MYSQL_CURSORCLASS` to use string value `'DictCursor'` instead of class reference

### 2. ✅ Login/Registration Internal Server Errors
**Problems**:
- Cursor not properly closed on exceptions, causing connection leaks
- No input validation, causing crashes on empty/malformed data
- No session timeout handling
- Poor error handling on server with different database configuration

**Solutions**:
- Added try-finally blocks to ensure cursors are always closed
- Added input validation for all registration and login fields
- Added `session.permanent = True` for proper session management
- Improved error messages for debugging

## Local Development Setup

```bash
# Environment variables (optional for local dev)
set MYSQL_HOST=localhost
set MYSQL_PORT=3308
set MYSQL_USER=root
set MYSQL_PASSWORD=
set MYSQL_DB=comic_learning_db

# Run the app
python app.py
```

## Server Deployment Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables (CRITICAL for production)

On Linux/Mac:
```bash
export FLASK_ENV=production
export SECRET_KEY="your-secure-random-key-here"
export MYSQL_HOST="your-database-host"
export MYSQL_USER="your-db-user"
export MYSQL_PASSWORD="your-db-password"
export MYSQL_DB="comic_learning_db"
export MYSQL_PORT="3306"  # Standard MySQL port
export UPLOAD_FOLDER="/var/www/comic_learning_app/static/uploads"
```

On Windows:
```powershell
$env:FLASK_ENV = "production"
$env:SECRET_KEY = "your-secure-random-key-here"
$env:MYSQL_HOST = "your-database-host"
$env:MYSQL_USER = "your-db-user"
$env:MYSQL_PASSWORD = "your-db-password"
$env:MYSQL_DB = "comic_learning_db"
$env:MYSQL_PORT = "3306"
$env:UPLOAD_FOLDER = "C:\var\www\comic_learning_app\static\uploads"
```

### 3. Create Uploads Directory
```bash
mkdir -p static/uploads/profiles
mkdir -p static/uploads/stories
mkdir -p static/uploads/chat
mkdir -p static/uploads/images
mkdir -p static/uploads/stories
mkdir -p static/uploads/story_audio
mkdir -p static/uploads/story_pages
mkdir -p static/uploads/story_videos
```

### 4. Database Setup
```bash
# Connect to MySQL and run schema
mysql -h your-host -u your-user -p your-password < database/schema.sql
```

### 5. Run with Gunicorn (Production)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or with more workers for high traffic
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 120 app:app
```

### 6. Use Nginx as Reverse Proxy (Recommended)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 500M;
    }

    location /static {
        alias /path/to/comic_learning_app/static;
        expires 30d;
    }
}
```

## Common Server Issues & Solutions

### Issue 1: "An error occurred during login" on Server
**Causes**:
- Database connection timeout
- Wrong database credentials in environment variables
- Database not running or unreachable

**Fix**:
```bash
# Test database connection
mysql -h your-host -u your-user -p your-password -D your-db -e "SELECT 1"
```

### Issue 2: Session Lost on Server
**Causes**:
- `SESSION_COOKIE_HTTPONLY` too strict
- Session not marked as permanent

**Already Fixed**: Session now uses `session.permanent = True`

### Issue 3: Connection Pool Exhaustion
**Symptoms**: Random timeouts after working initially

**Fix**: Cursor always closed with try-finally blocks (already implemented)

### Issue 4: File Upload Fails on Server
**Cause**: Uploads folder not writable or not set in environment

**Fix**:
```bash
# Ensure upload folder exists and is writable
chmod -R 755 static/uploads
chown www-data:www-data static/uploads
```

## Production Checklist

- [ ] Set all environment variables
- [ ] Create `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Test database connection from server
- [ ] Create uploads directory with proper permissions
- [ ] Use Gunicorn or similar WSGI server
- [ ] Set up Nginx reverse proxy
- [ ] Enable HTTPS with SSL certificate
- [ ] Configure database backups
- [ ] Monitor application logs
- [ ] Set up error alerting

## Logging

Production logs are available in the application output. Monitor these messages:
- `User logged in successfully` - Successful login
- `Login error:` - Login problems (check details in traceback)
- `Student registration error:` - Registration problems
- `Database connection check failed:` - Connection issues

## Security Notes

1. **Always use environment variables** for sensitive data (passwords, API keys)
2. **Never commit** `.env` files to version control
3. **Use HTTPS** in production (set `SESSION_COOKIE_SECURE=True`)
4. **Strong SECRET_KEY** - use `openssl rand -hex 32` to generate
5. **Database user** - use dedicated account with limited privileges

## Success Indicators

✅ Login page loads without errors
✅ Student registration completes with redirect to login
✅ Login succeeds with registered credentials
✅ Session persists across page navigation
✅ Logout clears session properly
✅ No database connection errors in logs
