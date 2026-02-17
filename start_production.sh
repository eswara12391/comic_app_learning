#!/bin/bash
# Deployment startup script for Comic Learning App
# Usage: ./start_production.sh

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "✓ Environment variables loaded from .env"
else
    echo "⚠ .env file not found. Using system environment variables."
    echo "ℹ Copy .env.example to .env and configure for your server"
fi

# Validate required environment variables
required_vars=("MYSQL_HOST" "MYSQL_USER" "MYSQL_DB" "SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo "❌ Error: The following required environment variables are not set:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "ℹ Please set these variables and try again."
    echo "ℹ See DEPLOY.md for instructions"
    exit 1
fi

# Test database connection
echo "Testing database connection..."
python3 -c "
import MySQLdb
try:
    conn = MySQLdb.connect(
        host='${MYSQL_HOST:-localhost}',
        user='${MYSQL_USER}',
        passwd='${MYSQL_PASSWORD:-}',
        db='${MYSQL_DB}'
    )
    conn.close()
    print('✓ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" || exit 1

# Create upload directories
echo "Creating upload directories..."
mkdir -p static/uploads/{profiles,stories,chat,images,story_audio,story_pages,story_videos}
chmod -R 755 static/uploads
echo "✓ Upload directories ready"

# Run production server with gunicorn
echo ""
echo "============================================"
echo "Starting Comic Learning App (Production)"
echo "============================================"
echo "Environment: production"
echo "Database: ${MYSQL_USER}@${MYSQL_HOST}:${MYSQL_PORT:-3306}/${MYSQL_DB}"
echo "Upload folder: ${UPLOAD_FOLDER:-static/uploads}"
echo ""
echo "Server running on: http://0.0.0.0:5000"
echo "Press Ctrl+C to stop"
echo "============================================"
echo ""

export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - app:app
