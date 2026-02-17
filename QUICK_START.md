# Quick Deployment Reference

## For Server Deployment - Do These Steps:

### Step 1: Copy Environment Template
```bash
cp .env.example .env
```

### Step 2: Update .env with Your Server Details
```env
FLASK_ENV=production
SECRET_KEY=<generate-with-openssl-rand-hex-32>
MYSQL_HOST=your-database-host
MYSQL_USER=your-database-user
MYSQL_PASSWORD=your-database-password
MYSQL_DB=comic_learning_db
MYSQL_PORT=3306
```

### Step 3: Generate Secure Secret Key

**Linux/Mac:**
```bash
openssl rand -hex 32
```

**Windows (Python):**
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Windows (PowerShell):**
```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RNGCryptoServiceProvider]::new().GetBytes($bytes)
$hex = -join ($bytes | ForEach-Object { $_.ToString('x2') })
Write-Output $hex
```

### Step 4: Verify Database Connection
```bash
mysql -h your-host -u your-user -p your-password -D comic_learning_db -e "SELECT 1"
```

### Step 5: Run the App

**Linux/Mac:**
```bash
chmod +x start_production.sh
./start_production.sh
```

**Windows:**
```cmd
start_production.bat
```

**Or Manual (any OS):**
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## What Was Fixed

| Issue | Local | Server | Fix |
|-------|-------|--------|-----|
| Login error | ✓ | ✗ | Proper cursor management, better error handling |
| Registration error | ✓ | ✗ | Input validation, session management |
| Connection timeout | N/A | ✗ | Added connection pooling settings |
| Generic error messages | N/A | ✗ | Detailed logging and error reporting |
| Session loss | ✓ | ✗ | Added `session.permanent = True` |

## Environment Variables (Critical for Server)

```env
# Database (MUST match your server database)
MYSQL_HOST=production.example.com
MYSQL_USER=db_user
MYSQL_PASSWORD=secure_password_here
MYSQL_DB=comic_learning_db
MYSQL_PORT=3306

# Security (MUST be unique for production)
SECRET_KEY=<your-secret-key>
FLASK_ENV=production

# Optional
UPLOAD_FOLDER=/var/www/comic_learning_app/static/uploads
MYSQL_CONNECTION_TIMEOUT=30
```

## Test After Deployment

1. Open: `http://your-server:5000/`
2. Try registration at: `/register/student`
3. Try login at: `/login`
4. Check logs for any errors

## Common Issues

| Issue | Solution |
|-------|----------|
| "An error occurred during login" | Check MYSQL credentials in .env |
| File uploads fail | Create uploads dir, set permissions |
| "SECRET_KEY must be set" | Generate and add to .env |
| Connection timeout | Check database is running, accessible |
| Page not found | Check app is running on correct port |

## Quick Troubleshooting

```bash
# Check if app is running
curl http://localhost:5000/

# Test database connection
mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DB -e "SELECT 1"

# View logs (Linux)
tail -f app.log

# Kill process (if needed)
pkill -f gunicorn
```

## Files to Read

- 📖 **DEPLOY.md** - Full deployment guide
- 📋 **FIXES_SUMMARY.md** - What was fixed and why
- ⚙️ **.env.example** - Template for environment variables
- 📝 **config.py** - Configuration options

---

**Key Takeaway**: All database credentials should be in environment variables on the server, NOT in code. Never commit .env file to version control.
