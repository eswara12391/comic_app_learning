# config.py
import os
from datetime import timedelta

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'comic-learning-application-secret-key-2026'
    
    # MySQL Database configuration
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # Empty password for XAMPP default
    MYSQL_DB = 'comic_learning_db'
    MYSQL_PORT = 3308  # Default MySQL port
    MYSQL_CURSORCLASS = 'DictCursor'  # Use DictCursor class name
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 50MB max upload for stories
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg'}
    
    # Security
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'password-salt'
    WTF_CSRF_ENABLED = True
    
    # Quiz settings
    MAX_QUESTIONS_PER_QUIZ = 10
    QUIZ_TIME_LIMIT = 600  # 10 minutes in seconds
    
    
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'production-secret-key')

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