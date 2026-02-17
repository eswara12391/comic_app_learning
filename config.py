# config.py
import os
from datetime import timedelta

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'comic-learning-application-secret-key-2026'
    
    # MySQL Database configuration - Support environment variables for server deployment
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')  # Empty for XAMPP, set env var on server
    MYSQL_DB = os.environ.get('MYSQL_DB', 'comic_learning_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3308))  # Default MySQL port, configurable for server
    MYSQL_CURSORCLASS = 'DictCursor'  # Use DictCursor class name
    MYSQL_USE_UNICODE = True
    MYSQL_CHARSET = 'utf8mb4'
    
    # Database connection pool settings
    MYSQL_CONNECTION_TIMEOUT = int(os.environ.get('MYSQL_CONNECTION_TIMEOUT', 30))
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'comic_app_session'
    PERMANENT_SESSION_SECURE = False
    
    # Application settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 50MB max upload for stories
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg'}
    
    # Security
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'password-salt'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False
    
    # Error handling
    PROPAGATE_EXCEPTIONS = True
    
    # Quiz settings
    MAX_QUESTIONS_PER_QUIZ = 10
    QUIZ_TIME_LIMIT = 600  # 10 minutes in seconds
    
    
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_SECURE = False
    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Use HTTPS only in production
    PERMANENT_SESSION_SECURE = True
    # Ensure these are set as environment variables on the server
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'comic_learning_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))  # Standard MySQL port for production
    SECRET_KEY = os.environ.get('SECRET_KEY')  # MUST be set on server
    
    # Raise error if SECRET_KEY not configured
    def __init__(self):
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    MYSQL_DB = 'comic_learning_test_db'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}