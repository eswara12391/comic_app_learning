@echo off
REM Deployment startup script for Comic Learning App (Windows)
REM Usage: start_production.bat

echo.
echo ============================================
echo Comic Learning App - Production Startup
echo ============================================
echo.

REM Load environment variables from .env file if it exists
if exist .env (
    echo Loading environment variables from .env...
    for /f "delims== tokens=1,2" %%a in (.env) do (
        if not "%%a"=="" (
            if not "%%a:~0,1%%"=="#" (
                set %%a=%%b
            )
        )
    )
    echo [OK] Environment variables loaded
) else (
    echo [WARNING] .env file not found
    echo Copy .env.example to .env and configure for your server
    echo.
)

REM Validate required environment variables
setlocal enabledelayedexpansion
set "missing_vars="

if "!MYSQL_HOST!"=="" set "missing_vars=!missing_vars! MYSQL_HOST"
if "!MYSQL_USER!"=="" set "missing_vars=!missing_vars! MYSQL_USER"
if "!MYSQL_DB!"=="" set "missing_vars=!missing_vars! MYSQL_DB"
if "!SECRET_KEY!"=="" set "missing_vars=!missing_vars! SECRET_KEY"

if not "!missing_vars!"=="" (
    echo [ERROR] Missing environment variables:
    for %%v in (!missing_vars!) do echo   - %%v
    echo.
    echo Please set these variables and try again.
    echo See DEPLOY.md for instructions
    pause
    exit /b 1
)

REM Test database connection
echo.
echo Testing database connection...
python -c "import MySQLdb; MySQLdb.connect(host='%MYSQL_HOST%', user='%MYSQL_USER%', passwd='%MYSQL_PASSWORD%', db='%MYSQL_DB%')" >nul 2>&1

if errorlevel 1 (
    echo [ERROR] Database connection failed
    echo Please check your MYSQL credentials and try again
    pause
    exit /b 1
)
echo [OK] Database connection successful

REM Create upload directories
echo.
echo Creating upload directories...
if not exist "static\uploads\profiles" mkdir "static\uploads\profiles"
if not exist "static\uploads\stories" mkdir "static\uploads\stories"
if not exist "static\uploads\chat" mkdir "static\uploads\chat"
if not exist "static\uploads\images" mkdir "static\uploads\images"
if not exist "static\uploads\story_audio" mkdir "static\uploads\story_audio"
if not exist "static\uploads\story_pages" mkdir "static\uploads\story_pages"
if not exist "static\uploads\story_videos" mkdir "static\uploads\story_videos"
echo [OK] Upload directories ready

REM Run production server with gunicorn
echo.
echo ============================================
echo Starting Comic Learning App (Production)
echo ============================================
echo Environment: production
echo Database: %MYSQL_USER%@%MYSQL_HOST%:%MYSQL_PORT%/%MYSQL_DB%
echo Upload folder: %UPLOAD_FOLDER%
echo.
echo Server running on: http://0.0.0.0:5000
echo Press Ctrl+C to stop
echo ============================================
echo.

set FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app

pause
