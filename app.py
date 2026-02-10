# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file, abort, make_response
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime, timedelta
import uuid
from functools import wraps
from config import config
import time
import math
from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
from PIL import Image as PILImage
import random
import re
from functools import wraps


# # Import the StudentDrawing model
# from models import StudentDrawing, db


app = Flask(__name__)
app.config.from_object(config['development'])



# Initialize MySQL
mysql = MySQL(app)


# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'stories'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'chat'), exist_ok=True)


# Helper functions
def allowed_file(filename, file_type='image'):
    if file_type == 'image':
        allowed_extensions = app.config['ALLOWED_IMAGE_EXTENSIONS']
    elif file_type == 'audio':
        allowed_extensions = app.config['ALLOWED_AUDIO_EXTENSIONS']
    else:
        allowed_extensions = app.config['ALLOWED_IMAGE_EXTENSIONS']
    
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# def save_file(file, folder):
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         unique_filename = f"{uuid.uuid4().hex}_{filename}"
#         filepath = os.path.join(folder, unique_filename)
#         file.save(filepath)
#         return unique_filename
#     return None

def save_file(file, folder, file_type='image'):
    if file and allowed_file(file.filename, file_type):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(folder, unique_filename)
        file.save(filepath)
        return unique_filename
    return None

def get_student_id():
    if 'user_id' in session and session.get('user_type') == 'student':
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        cur.close()
        return student['id'] if student else None
    return None

def get_teacher_id():
    if 'user_id' in session and session.get('user_type') == 'teacher':
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
        teacher = cur.fetchone()
        cur.close()
        return teacher['id'] if teacher else None
    return None

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'teacher':
            flash('Access denied. Teacher privileges required.', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'student':
            flash('Access denied. Student privileges required.', 'danger')
            return redirect(url_for('teacher_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        if session['user_type'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('index.html')

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['user_type'] = user['user_type']
            
            # Update last login
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
            mysql.connection.commit()
            cur.close()
            
            flash(f'Welcome back!', 'success')
            
            if user['user_type'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        try:
            # User account details
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('register_student'))
            
            # Check if email exists
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash('Email already registered', 'danger')
                cur.close()
                return redirect(url_for('register_student'))
            
            # Create user account
            password_hash = generate_password_hash(password)
            cur.execute("INSERT INTO users (email, password_hash, user_type) VALUES (%s, %s, 'student')",
                       (email, password_hash))
            user_id = cur.lastrowid
            
            # Student details
            first_name = request.form.get('first_name')
            middle_name = request.form.get('middle_name')
            last_name = request.form.get('last_name')
            date_of_birth = request.form.get('date_of_birth')
            phone = request.form.get('phone')
            address = request.form.get('address')
            gender = request.form.get('gender')
            class_level = request.form.get('class_level')
            roll_number = request.form.get('roll_number')
            
            # Parent/Guardian details
            parent_full_name = request.form.get('parent_full_name')
            parent_email = request.form.get('parent_email')
            parent_phone = request.form.get('parent_phone')
            parent_relationship = request.form.get('parent_relationship')
            
            # Profile photo
            profile_photo = None
            if 'profile_photo' in request.files:
                file = request.files['profile_photo']
                if file and file.filename != '':
                    profile_photo = save_file(file, os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'))
            
            # Insert student details
            cur.execute("""
                INSERT INTO students 
                (user_id, first_name, middle_name, last_name, date_of_birth, phone, address, 
                 gender, class_level, roll_number, profile_photo, parent_full_name, 
                 parent_email, parent_phone, parent_relationship)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, first_name, middle_name, last_name, date_of_birth, phone, address,
                  gender, class_level, roll_number, profile_photo, parent_full_name,
                  parent_email, parent_phone, parent_relationship))
            
            mysql.connection.commit()
            cur.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('register_student'))
    
    return render_template('auth/register_student.html')

@app.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    if request.method == 'POST':
        try:
            # User account details
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('register_teacher'))
            
            # Check if email exists
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                flash('Email already registered', 'danger')
                cur.close()
                return redirect(url_for('register_teacher'))
            
            # Create user account
            password_hash = generate_password_hash(password)
            cur.execute("INSERT INTO users (email, password_hash, user_type) VALUES (%s, %s, 'teacher')",
                       (email, password_hash))
            user_id = cur.lastrowid
            
            # Teacher details
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            date_of_birth = request.form.get('date_of_birth')
            address = request.form.get('address')
            gender = request.form.get('gender')
            registration_number = request.form.get('registration_number')
            
            # Profile photo
            profile_photo = None
            if 'profile_photo' in request.files:
                file = request.files['profile_photo']
                if file and file.filename != '':
                    profile_photo = save_file(file, os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'))
            
            # Insert teacher details
            cur.execute("""
                INSERT INTO teachers 
                (user_id, first_name, last_name, email, phone, date_of_birth, address, 
                 gender, registration_number, profile_photo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, first_name, last_name, email, phone, date_of_birth, address,
                  gender, registration_number, profile_photo))
            
            mysql.connection.commit()
            cur.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('register_teacher'))
    
    return render_template('auth/register_teacher.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ================================= Student Drawing =========================================================

@app.route('/api/save_student_drawing', methods=['POST'])
def save_student_drawing():
    """Save student's private drawing to database"""
    try:
        data = request.get_json()
        story_id = data.get('story_id')
        drawing_data = data.get('drawing_data')
        
        if not all([story_id, drawing_data]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        
        if not student:
            cur.close()
            return jsonify({'success': False, 'error': 'Student not found'}), 404
            
        student_id = student['id']
        
        # Check if drawing exists
        cur.execute("SELECT id FROM student_drawings WHERE story_id = %s AND student_id = %s", 
                   (story_id, student_id))
        existing = cur.fetchone()
        
        current_time = datetime.utcnow()
        
        if existing:
            cur.execute("UPDATE student_drawings SET drawing_data = %s, updated_at = %s WHERE id = %s",
                       (drawing_data, current_time, existing['id']))
            message = 'Drawing updated'
        else:
            cur.execute("INSERT INTO student_drawings (story_id, student_id, drawing_data, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                       (story_id, student_id, drawing_data, current_time, current_time))
            message = 'Drawing saved'
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        print(f"Error saving drawing: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get_student_drawing', methods=['GET'])
def get_student_drawing():
    """Get student's private drawing from database"""
    try:
        story_id = request.args.get('story_id', type=int)
        
        if not story_id:
            return jsonify({'success': False, 'error': 'Missing story_id'}), 400
        
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        
        if not student:
            cur.close()
            return jsonify({'success': False, 'error': 'Student not found'}), 404
            
        student_id = student['id']
        
        cur.execute("SELECT drawing_data FROM student_drawings WHERE story_id = %s AND student_id = %s", 
                   (story_id, student_id))
        drawing = cur.fetchone()
        cur.close()
        
        if drawing:
            return jsonify({'success': True, 'drawing_data': drawing['drawing_data']})
        else:
            return jsonify({'success': True, 'drawing_data': None})
            
    except Exception as e:
        print(f"Error getting drawing: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear_student_drawing', methods=['POST'])
def clear_student_drawing():
    """Clear student's drawing (save empty canvas)"""
    try:
        data = request.get_json()
        story_id = data.get('story_id')
        
        if not story_id:
            return jsonify({'success': False, 'error': 'Missing story_id'}), 400
        
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        
        cur = mysql.connection.cursor()
        
        # Get student_id from students table
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        
        if not student:
            cur.close()
            return jsonify({'success': False, 'error': 'Student not found'}), 404
            
        student_id = student['id']
        
        # Create a blank canvas data URL (transparent 1x1 pixel)
        blank_canvas_data = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        
        # Check if drawing already exists
        cur.execute("""
            SELECT id FROM student_drawings 
            WHERE story_id = %s AND student_id = %s
        """, (story_id, student_id))
        
        existing_drawing = cur.fetchone()
        
        current_time = datetime.utcnow()
        
        if existing_drawing:
            # Update with blank canvas
            cur.execute("""
                UPDATE student_drawings 
                SET drawing_data = %s, updated_at = %s
                WHERE id = %s
            """, (blank_canvas_data, current_time, existing_drawing['id']))
        else:
            # Create new blank drawing
            cur.execute("""
                INSERT INTO student_drawings 
                (story_id, student_id, drawing_data, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (story_id, student_id, blank_canvas_data, current_time, current_time))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Drawing cleared successfully'
        })
        
    except Exception as e:
        if 'cur' in locals():
            mysql.connection.rollback()
            cur.close()
        print(f"Error clearing drawing: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    


#========================================== Student<-> Teacher chat routes ================================================
def get_current_teacher_id():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id 
        FROM teachers 
        WHERE user_id = %s
    """, (session['user_id'],))
    row = cur.fetchone()
    cur.close()
    return row['id'] if row else None


def get_or_create_conversation(teacher_id, student_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id FROM chat_conversations 
        WHERE teacher_id=%s AND student_id=%s
    """, (teacher_id, student_id))
    row = cur.fetchone()

    if row:
        return row['id']

    cur.execute("""
        INSERT INTO chat_conversations (teacher_id, student_id)
        VALUES (%s, %s)
    """, (teacher_id, student_id))
    mysql.connection.commit()
    return cur.lastrowid

# @app.route('/api/chat/send', methods=['POST'])
# @login_required
# def send_chat_message():
#     data = request.json
#     conversation_id = data['conversation_id']
#     message = data['message']

#     user_type = session['user_type']
#     sender_id = session['user_id']

#     cur = mysql.connection.cursor()
#     cur.execute("""
#         INSERT INTO chat_messages 
#         (conversation_id, sender_type, sender_id, message, is_read)
#         VALUES (%s, %s, %s, %s, FALSE)
#     """, (conversation_id, user_type, sender_id, message))

#     mysql.connection.commit()
#     cur.close()
    
#     return jsonify({'success': True})
@app.route('/api/chat/send', methods=['POST'])
@login_required
def send_chat_message():
    data = request.json
    conversation_id = data['conversation_id']
    message = data['message']

    user_type = session['user_type']
    user_id = session['user_id']

    cur = mysql.connection.cursor()

    try:
        # Validate conversation ownership
        if user_type == 'teacher':
            teacher_id = get_current_teacher_id()
            cur.execute("""
                SELECT id FROM chat_conversations
                WHERE id = %s AND teacher_id = %s
            """, (conversation_id, teacher_id))
        else:
            cur.execute("""
                SELECT s.id as student_id
                FROM students s
                WHERE s.user_id = %s
            """, (user_id,))
            row = cur.fetchone()
            student_id = row['student_id']

            cur.execute("""
                SELECT id FROM chat_conversations
                WHERE id = %s AND student_id = %s
            """, (conversation_id, student_id))

        if not cur.fetchone():
            return jsonify({'success': False, 'error': 'Invalid conversation'}), 403

        cur.execute("""
            INSERT INTO chat_messages 
            (conversation_id, sender_type, sender_id, message, is_read)
            VALUES (%s, %s, %s, %s, FALSE)
        """, (conversation_id, user_type, user_id, message))

        mysql.connection.commit()
        return jsonify({'success': True})

    finally:
        cur.close()

@app.route('/api/chat/messages/<int:conversation_id>')
@login_required
def get_chat_messages(conversation_id):
    cur = None
    try:
        cur = mysql.connection.cursor()
        
        # Simple query without DATE_FORMAT to avoid % issues
        cur.execute("""
            SELECT sender_type, message, created_at
            FROM chat_messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        messages = cur.fetchall()
        
        # Format messages for JSON response
        result = []
        for msg in messages:
            result.append({
                'sender_type': msg['sender_type'],
                'message': msg['message'],
                'created_at': msg['created_at'].isoformat() if msg['created_at'] else None
            })
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching chat messages: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cur:
            cur.close()

# @app.route('/api/chat/unread-count')
# @login_required
# def get_unread_count():
#     cur = mysql.connection.cursor()
    
#     try:
#         if session['user_type'] == 'teacher':
#             cur.execute("""
#                 SELECT COUNT(cm.id) as count
#                 FROM chat_messages cm
#                 JOIN chat_conversations cc ON cm.conversation_id = cc.id
#                 WHERE cc.teacher_id = %s 
#                   AND cm.sender_type = 'student'
#                   AND cm.is_read = FALSE
#             """, (session['user_id'],))
#         else:  # student
#             cur.execute("""
#                 SELECT COUNT(cm.id) as count
#                 FROM chat_messages cm
#                 JOIN chat_conversations cc ON cm.conversation_id = cc.id
#                 WHERE cc.student_id = %s 
#                   AND cm.sender_type = 'teacher'
#                   AND cm.is_read = FALSE
#             """, (session['user_id'],))
        
#         result = cur.fetchone()
#         count = result['count'] if result and result['count'] else 0
        
#         return jsonify({'count': count, 'success': True})
        
#     except Exception as e:
#         print(f"Error getting unread count: {str(e)}")
#         return jsonify({'count': 0, 'success': False, 'error': str(e)})
#     finally:
#         cur.close()
@app.route('/api/chat/unread-count')
@login_required
def get_unread_count():
    cur = mysql.connection.cursor()

    try:
        if session['user_type'] == 'teacher':
            teacher_id = get_current_teacher_id()

            if not teacher_id:
                return jsonify({'count': 0, 'success': True})

            cur.execute("""
                SELECT COUNT(cm.id) as count
                FROM chat_messages cm
                JOIN chat_conversations cc ON cm.conversation_id = cc.id
                WHERE cc.teacher_id = %s
                  AND cm.sender_type = 'student'
                  AND cm.is_read = FALSE
            """, (teacher_id,))

        else:  # student
            # student_id is stored in students table, NOT users
            cur.execute("""
                SELECT s.id as student_id
                FROM students s
                WHERE s.user_id = %s
            """, (session['user_id'],))
            row = cur.fetchone()
            student_id = row['student_id'] if row else None

            if not student_id:
                return jsonify({'count': 0, 'success': True})

            cur.execute("""
                SELECT COUNT(cm.id) as count
                FROM chat_messages cm
                JOIN chat_conversations cc ON cm.conversation_id = cc.id
                WHERE cc.student_id = %s
                  AND cm.sender_type = 'teacher'
                  AND cm.is_read = FALSE
            """, (student_id,))

        result = cur.fetchone()
        count = result['count'] if result and result['count'] else 0

        return jsonify({'count': count, 'success': True})

    except Exception as e:
        print(f"Error getting unread count: {str(e)}")
        return jsonify({'count': 0, 'success': False, 'error': str(e)})

    finally:
        cur.close()

# @app.route('/api/chat/mark-read/<int:conversation_id>', methods=['POST'])
# @login_required
# def mark_messages_as_read(conversation_id):
#     cur = mysql.connection.cursor()
    
#     try:
#         if session['user_type'] == 'teacher':
#             cur.execute("""
#                 UPDATE chat_messages 
#                 SET is_read = TRUE 
#                 WHERE conversation_id = %s 
#                   AND sender_type = 'student'
#                   AND is_read = FALSE
#             """, (conversation_id,))
#         else:  # student
#             cur.execute("""
#                 UPDATE chat_messages 
#                 SET is_read = TRUE 
#                 WHERE conversation_id = %s 
#                   AND sender_type = 'teacher'
#                   AND is_read = FALSE
#             """, (conversation_id,))
        
#         mysql.connection.commit()
#         return jsonify({'success': True})
        
#     except Exception as e:
#         print(f"Error marking messages as read: {str(e)}")
#         return jsonify({'success': False, 'error': str(e)})
#     finally:
#         cur.close()
@app.route('/api/chat/mark-read/<int:conversation_id>', methods=['POST'])
@login_required
def mark_messages_as_read(conversation_id):
    cur = mysql.connection.cursor()

    try:
        if session['user_type'] == 'teacher':
            teacher_id = get_current_teacher_id()

            if not teacher_id:
                return jsonify({'success': True})

            cur.execute("""
                UPDATE chat_messages 
                SET is_read = TRUE 
                WHERE conversation_id = %s
                  AND sender_type = 'student'
                  AND is_read = FALSE
            """, (conversation_id,))

        else:  # student
            cur.execute("""
                SELECT s.id as student_id
                FROM students s
                WHERE s.user_id = %s
            """, (session['user_id'],))
            row = cur.fetchone()
            student_id = row['student_id'] if row else None

            if not student_id:
                return jsonify({'success': True})

            cur.execute("""
                UPDATE chat_messages 
                SET is_read = TRUE 
                WHERE conversation_id = %s
                  AND sender_type = 'teacher'
                  AND is_read = FALSE
            """, (conversation_id,))

        mysql.connection.commit()
        return jsonify({'success': True})

    except Exception as e:
        print(f"Error marking messages as read: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

    finally:
        cur.close()

@app.route('/api/chat/teacher/unread-by-student')
@login_required
def get_teacher_unread_by_student():
    if session['user_type'] != 'teacher':
        return jsonify([])

    teacher_id = get_current_teacher_id()
    cur = mysql.connection.cursor()

    try:
        cur.execute("""
            SELECT 
                s.id as student_id,
                s.first_name,
                s.last_name,
                COUNT(cm.id) as unread_count,
                MAX(cm.created_at) as last_message_time
            FROM chat_messages cm
            JOIN chat_conversations cc ON cm.conversation_id = cc.id
            JOIN students s ON cc.student_id = s.id
            WHERE cc.teacher_id = %s
              AND cm.sender_type = 'student'
              AND cm.is_read = FALSE
            GROUP BY s.id
            ORDER BY last_message_time DESC
        """, (teacher_id,))

        rows = cur.fetchall()
        return jsonify(rows)

    finally:
        cur.close()



# ====================================== Student<->Student chat routes ====================================


def get_current_student_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
    student = cur.fetchone()
    cur.close()
    return student['id'] if student else None

# @app.route('/api/student/classmates')
# @student_required
# def get_student_classmates():
#     cur = mysql.connection.cursor()

#     print("DEBUG session user_id:", session.get('user_id'))

#     student_id = get_current_student_id()
#     print("DEBUG student_id:", student_id)

#     if not student_id:
#         cur.close()
#         return jsonify([])

#     # Get my class
#     cur.execute("""
#         SELECT class_level 
#         FROM students 
#         WHERE id = %s
#     """, (student_id,))
    
#     me = cur.fetchone()
#     print("DEBUG me:", me)

#     if not me:
#         cur.close()
#         return jsonify([])

#     my_class = me['class_level']
#     print("DEBUG my_class repr:", repr(my_class))

#     # BULLETPROOF class match
#     cur.execute("""
#         SELECT id, first_name, last_name, roll_number, class_level
#         FROM students
#         WHERE LOWER(TRIM(class_level)) = LOWER(TRIM(%s))
#           AND id != %s
#         ORDER BY first_name
#     """, (my_class, student_id))

#     classmates = cur.fetchall()
#     print("DEBUG classmates:", classmates)

#     cur.close()

#     return jsonify(classmates)
@app.route('/api/student/classmates')
@student_required
def get_student_classmates():
    cur = mysql.connection.cursor()

    student_id = get_current_student_id()
    if not student_id:
        cur.close()
        return jsonify([])

    # Get my class
    cur.execute("SELECT class_level FROM students WHERE id = %s", (student_id,))
    me = cur.fetchone()
    if not me:
        cur.close()
        return jsonify([])

    my_class = me['class_level']

    # Get classmates + conversation + unread count
    cur.execute("""
        SELECT 
            s.id,
            s.first_name,
            s.last_name,
            sc.id AS conversation_id,

            -- Unread count from this classmate
            SUM(
                CASE 
                    WHEN sm.is_read = FALSE 
                     AND sm.sender_id = s.id 
                    THEN 1 ELSE 0 
                END
            ) AS unread_count

        FROM students s

        LEFT JOIN student_conversations sc
          ON (
                (sc.student1_id = %s AND sc.student2_id = s.id)
             OR (sc.student2_id = %s AND sc.student1_id = s.id)
          )

        LEFT JOIN student_messages sm
          ON sm.conversation_id = sc.id

        WHERE LOWER(TRIM(s.class_level)) = LOWER(TRIM(%s))
          AND s.id != %s

        GROUP BY s.id, sc.id
        ORDER BY s.first_name
    """, (student_id, student_id, my_class, student_id))

    classmates = cur.fetchall()
    cur.close()

    # Convert None to 0
    for c in classmates:
        c['unread_count'] = int(c['unread_count'] or 0)

    return jsonify(classmates)

@app.route('/api/student-chat/start/<int:classmate_id>')
@student_required
def start_student_chat(classmate_id):
    cur = mysql.connection.cursor()

    student_id = get_current_student_id()
    if not student_id:
        cur.close()
        return jsonify({'success': False})

    s1 = min(student_id, classmate_id)
    s2 = max(student_id, classmate_id)

    cur.execute("""
        SELECT id FROM student_conversations
        WHERE student1_id = %s AND student2_id = %s
    """, (s1, s2))

    convo = cur.fetchone()

    if convo:
        conversation_id = convo['id']
    else:
        cur.execute("""
            INSERT INTO student_conversations (student1_id, student2_id)
            VALUES (%s, %s)
        """, (s1, s2))
        mysql.connection.commit()
        conversation_id = cur.lastrowid

    cur.close()

    return jsonify({"success": True, "conversation_id": conversation_id})

@app.route('/api/student-chat/send', methods=['POST'])
@student_required
def send_student_chat_message():
    data = request.json
    conversation_id = data.get('conversation_id')
    message = data.get('message')

    if not conversation_id or not message:
        return jsonify({'success': False}), 400

    student_id = get_current_student_id()
    if not student_id:
        return jsonify({'success': False}), 400

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO student_messages (conversation_id, sender_id, message, is_read)
        VALUES (%s, %s, %s, FALSE)
    """, (conversation_id, student_id, message))

    mysql.connection.commit()
    cur.close()

    return jsonify({'success': True})

@app.route('/api/student-chat/messages/<int:conversation_id>')
@student_required
def get_student_chat_messages(conversation_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, sender_id, message, created_at, is_read
        FROM student_messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
    """, (conversation_id,))

    messages = cur.fetchall()
    cur.close()

    # Convert datetime to string
    formatted_messages = []
    for m in messages:
        formatted_messages.append({
            'id': m['id'],
            'sender_id': m['sender_id'],
            'message': m['message'],
            'created_at': m['created_at'].strftime('%Y-%m-%d %H:%M:%S'),  # <-- format
            'is_read': bool(m['is_read'])
        })

    return jsonify(formatted_messages)

@app.route('/api/student-chat/unread-count')
@student_required
def get_student_chat_unread_count():
    cur = mysql.connection.cursor()

    student_id = get_current_student_id()
    if not student_id:
        cur.close()
        return jsonify({'count': 0})

    cur.execute("""
        SELECT COUNT(*) as count
        FROM student_messages sm
        JOIN student_conversations sc ON sm.conversation_id = sc.id
        WHERE (sc.student1_id = %s OR sc.student2_id = %s)
          AND sm.sender_id != %s
          AND sm.is_read = FALSE
    """, (student_id, student_id, student_id))

    result = cur.fetchone()
    count = result['count'] if result and result['count'] else 0

    cur.close()
    return jsonify({'count': count, 'success': True})

@app.route('/api/student-chat/mark-read/<int:conversation_id>', methods=['POST'])
@student_required
def mark_student_messages_read(conversation_id):
    cur = mysql.connection.cursor()

    student_id = get_current_student_id()
    if not student_id:
        cur.close()
        return jsonify({'success': False})

    cur.execute("""
        UPDATE student_messages
        SET is_read = TRUE
        WHERE conversation_id = %s
          AND sender_id != %s
    """, (conversation_id, student_id))

    mysql.connection.commit()
    cur.close()

    return jsonify({'success': True})


##================================== puzzel =================================================


# new Helper function to generate puzzles from text content
def generate_puzzle_from_text(text_content, puzzle_type='word_search'):
    """Generate a puzzle based on text content"""
    # Extract important words from text
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text_content.lower())
    words = list(set(words))[:6]  # Get unique words, max 6
    
    if len(words) < 3:
        # If not enough words, use common words
        words = ['learn', 'story', 'read', 'book', 'page', 'text', 'comic', 'picture']
    
    puzzle_data = {}
    
    if puzzle_type == 'word_search':
        puzzle_data = {
            'type': 'word_search',
            'grid_size': 8,
            'words': words,
            'directions': ['horizontal', 'vertical'],
            'hint': 'Find these words in the grid: ' + ', '.join(words)
        }
    
    elif puzzle_type == 'fill_blank':
        # Create fill in the blanks from sentences
        sentences = [s.strip() for s in text_content.split('.') if len(s.strip()) > 20]
        if len(sentences) > 3:
            sentences = sentences[:3]
        
        blanks = []
        for sentence in sentences:
            # Replace some words with blanks
            words_in_sentence = sentence.split()
            if len(words_in_sentence) > 5:
                # Choose 1-2 words to blank out
                num_blanks = min(2, len(words_in_sentence) - 4)
                blank_indices = random.sample(range(4, len(words_in_sentence) - 1), num_blanks)
                
                blank_sentence = words_in_sentence.copy()
                answers = []
                for idx in blank_indices:
                    answers.append(words_in_sentence[idx])
                    blank_sentence[idx] = '_____'
                
                blanks.append({
                    'sentence': ' '.join(blank_sentence),
                    'answers': answers  # This will be a list with 2 answers if 2 blanks
                })
        
        puzzle_data = {
            'type': 'fill_blank',
            'blanks': blanks,
            'hint': 'Fill in the blanks with words from the story'
        }
    
    elif puzzle_type == 'multiple_choice':
        # Create multiple choice questions
        sentences = [s.strip() for s in text_content.split('.') if len(s.strip()) > 15]
        questions = []
        
        for sentence in sentences[:3]:
            words = sentence.split()
            if len(words) > 5:
                correct_word = random.choice([w for w in words if len(w) > 3])
                question_text = sentence.replace(correct_word, '_____')
                
                # Generate wrong options
                wrong_words = [w for w in words if w != correct_word and len(w) > 3][:3]
                while len(wrong_words) < 3:
                    wrong_words.append(random.choice(['wrong', 'incorrect', 'false', 'bad']))
                
                options = [correct_word] + wrong_words[:3]
                random.shuffle(options)
                
                questions.append({
                    'question': question_text,
                    'options': options,
                    'correct_answer': correct_word
                })
        
        puzzle_data = {
            'type': 'multiple_choice',
            'questions': questions,
            'hint': 'Choose the correct word to complete the sentence'
        }
    
    elif puzzle_type == 'true_false':
        # Create true/false statements
        sentences = [s.strip() for s in text_content.split('.') if len(s.strip()) > 10]
        statements = []
        
        for sentence in sentences[:4]:
            # Make some true, some false
            is_true = random.choice([True, False])
            if not is_true:
                # Modify sentence to make it false
                words = sentence.split()
                if len(words) > 3:
                    # Change a word to make it incorrect
                    idx = random.randint(0, len(words) - 1)
                    original_word = words[idx]
                    # Try to find a similar but wrong word
                    alternatives = {
                        'is': 'is not',
                        'are': 'are not',
                        'was': 'was not',
                        'were': 'were not',
                        'has': 'has not',
                        'have': 'have not',
                        'can': 'cannot'
                    }
                    if original_word.lower() in alternatives:
                        words[idx] = alternatives[original_word.lower()]
                    else:
                        words[idx] = 'NOT_' + original_word
                    modified_sentence = ' '.join(words)
                    statements.append({
                        'statement': modified_sentence,
                        'answer': False
                    })
            else:
                statements.append({
                    'statement': sentence,
                    'answer': True
                })
        
        puzzle_data = {
            'type': 'true_false',
            'statements': statements,
            'hint': 'Determine if each statement is True or False based on the story'
        }
    
    return puzzle_data

# # API to submit puzzle answer
# @app.route('/api/submit_puzzle_answer', methods=['POST'])
# @student_required
# def submit_puzzle_answer():
#     try:
#         data = request.json
#         puzzle_id = data.get('puzzle_id')
#         answers = data.get('answers', {})
        
#         if not puzzle_id:
#             return jsonify({'success': False, 'error': 'Puzzle ID required'})
        
#         cur = mysql.connection.cursor()
        
#         # Get puzzle data
#         cur.execute("""
#             SELECT spp.*, pt.name as puzzle_type
#             FROM story_page_puzzles spp
#             JOIN puzzle_types pt ON spp.puzzle_type_id = pt.id
#             WHERE spp.id = %s
#         """, (puzzle_id,))
        
#         puzzle = cur.fetchone()
        
#         if not puzzle:
#             return jsonify({'success': False, 'error': 'Puzzle not found'})
        
#         # Get student ID
#         cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
#         student = cur.fetchone()
#         student_id = student['id']
        
#         # Parse puzzle data
#         puzzle_data = json.loads(puzzle['puzzle_data'])
#         puzzle_type = puzzle['puzzle_type']
        
#         # Calculate score based on puzzle type
#         score = 0
#         total_questions = 0
#         results = {}
        
#         if puzzle_type == 'multiple_choice':
#             questions = puzzle_data.get('questions', [])
#             total_questions = len(questions)
            
#             for i, question in enumerate(questions):
#                 user_answer = answers.get(f'q{i}')
#                 correct_answer = question.get('correct_answer')
                
#                 if user_answer and user_answer.lower() == correct_answer.lower():
#                     score += 1
#                     results[f'q{i}'] = {'correct': True, 'correct_answer': correct_answer}
#                 else:
#                     results[f'q{i}'] = {'correct': False, 'correct_answer': correct_answer}
        
#         elif puzzle_type == 'true_false':
#             statements = puzzle_data.get('statements', [])
#             total_questions = len(statements)
            
#             for i, statement in enumerate(statements):
#                 user_answer = answers.get(f'q{i}')
#                 correct_answer = statement.get('answer')
                
#                 if user_answer is not None:
#                     user_bool = user_answer.lower() in ['true', '1', 'yes']
#                     if user_bool == correct_answer:
#                         score += 1
#                         results[f'q{i}'] = {'correct': True, 'correct_answer': 'True' if correct_answer else 'False'}
#                     else:
#                         results[f'q{i}'] = {'correct': False, 'correct_answer': 'True' if correct_answer else 'False'}
        
#         elif puzzle_type == 'fill_blank':
#             blanks = puzzle_data.get('blanks', [])
#             total_questions = len(blanks)
            
#             for i, blank in enumerate(blanks):
#                 user_answer = answers.get(f'q{i}', '').strip().lower()
#                 correct_answers = [ans.lower() for ans in blank.get('answers', [])]
                
#                 if user_answer in correct_answers:
#                     score += 1
#                     results[f'q{i}'] = {'correct': True, 'correct_answer': blank['answers'][0]}
#                 else:
#                     results[f'q{i}'] = {'correct': False, 'correct_answer': blank['answers'][0]}
        
#         elif puzzle_type == 'word_search':
#             # For word search, check if all words were found
#             words = puzzle_data.get('words', [])
#             total_questions = len(words)
            
#             for i, word in enumerate(words):
#                 user_found = answers.get(f'word_{i}', False)
#                 if user_found:
#                     score += 1
#                     results[f'word_{i}'] = {'correct': True, 'word': word}
#                 else:
#                     results[f'word_{i}'] = {'correct': False, 'word': word}
        
#         # Calculate percentage
#         if total_questions > 0:
#             percentage = (score / total_questions) * 100
#         else:
#             percentage = 0
        
#         # Check if passed
#         required_score = puzzle.get('required_score', 70)
#         passed = percentage >= required_score
        
#         # Get existing progress
#         cur.execute("""
#             SELECT * FROM student_puzzle_progress
#             WHERE student_id = %s AND puzzle_id = %s
#         """, (student_id, puzzle_id))
        
#         existing_progress = cur.fetchone()
        
#         if existing_progress:
#             # Update existing progress
#             cur.execute("""
#                 UPDATE student_puzzle_progress
#                 SET attempts = attempts + 1,
#                     best_score = GREATEST(best_score, %s),
#                     completed = %s,
#                     completed_at = CASE WHEN %s = TRUE THEN NOW() ELSE completed_at END
#                 WHERE student_id = %s AND puzzle_id = %s
#             """, (percentage, passed, passed, student_id, puzzle_id))
#         else:
#             # Create new progress
#             cur.execute("""
#                 INSERT INTO student_puzzle_progress
#                 (student_id, puzzle_id, attempts, best_score, completed, completed_at)
#                 VALUES (%s, %s, 1, %s, %s, %s)
#             """, (student_id, puzzle_id, percentage, passed, datetime.now() if passed else None))
        
#         mysql.connection.commit()
        
#         # If passed, update story progress to next page
#         if passed:
#             # Get story page info
#             cur.execute("""
#                 SELECT sp.story_id, sp.page_number
#                 FROM story_page_puzzles spp
#                 JOIN story_pages sp ON spp.story_page_id = sp.id
#                 WHERE spp.id = %s
#             """, (puzzle_id,))
            
#             page_info = cur.fetchone()
            
#             if page_info:
#                 story_id = page_info['story_id']
#                 current_page = page_info['page_number']
                
#                 # Get total pages
#                 cur.execute("SELECT COUNT(*) as total FROM story_pages WHERE story_id = %s", (story_id,))
#                 total_pages = cur.fetchone()['total']
                
#                 # Check if this is the last page
#                 is_last_page = current_page >= total_pages
                
#                 if not is_last_page:
#                     # Update to next page
#                     cur.execute("""
#                         UPDATE student_progress
#                         SET current_page = %s
#                         WHERE student_id = %s AND story_id = %s
#                     """, (current_page + 1, student_id, story_id))
#                     mysql.connection.commit()
                
#                 return jsonify({
#                     'success': True,
#                     'passed': True,
#                     'score': percentage,
#                     'required_score': required_score,
#                     'next_page': not is_last_page,
#                     'results': results,
#                     'message': f'Great! You scored {percentage:.1f}%. Moving to next page...'
#                 })
        
#         return jsonify({
#             'success': True,
#             'passed': passed,
#             'score': percentage,
#             'required_score': required_score,
#             'results': results,
#             'message': f'You scored {percentage:.1f}%. Need {required_score}% to pass. Try again!' if not passed else f'Great! You scored {percentage:.1f}%'
#         })
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)})

@app.route('/api/submit_puzzle_answer', methods=['POST'])
@student_required
def submit_puzzle_answer():
    try:
        data = request.json
        puzzle_id = data.get('puzzle_id')
        answers = data.get('answers', {})

        if not puzzle_id:
            return jsonify({'success': False, 'error': 'Puzzle ID required'})

        cur = mysql.connection.cursor()

        # Get puzzle data
        cur.execute("""
            SELECT spp.*, pt.name as puzzle_type
            FROM story_page_puzzles spp
            JOIN puzzle_types pt ON spp.puzzle_type_id = pt.id
            WHERE spp.id = %s
        """, (puzzle_id,))
        puzzle = cur.fetchone()

        if not puzzle:
            return jsonify({'success': False, 'error': 'Puzzle not found'})

        # Get student ID
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        student_id = student['id']

        puzzle_data = json.loads(puzzle['puzzle_data'])
        puzzle_type = puzzle['puzzle_type']

        score = 0
        total_questions = 0
        results = {}

        print("DEBUG USER ANSWERS:", answers)
        print("DEBUG PUZZLE DATA:", puzzle_data)

        # ---------------- MULTIPLE CHOICE ----------------
        if puzzle_type == 'multiple_choice':
            questions = puzzle_data.get('questions', [])
            total_questions = len(questions)

            for i, question in enumerate(questions):
                user_answer = str(answers.get(f'q{i}', '')).strip().lower()
                correct_answer = str(question.get('correct_answer', '')).strip().lower()

                if user_answer == correct_answer:
                    score += 1
                    results[f'q{i}'] = {
                        'correct': True, 
                        'correct_answer': question.get('correct_answer'),
                        'student_answer': answers.get(f'q{i}', '')
                    }
                else:
                    results[f'q{i}'] = {
                        'correct': False, 
                        'correct_answer': question.get('correct_answer'),
                        'student_answer': answers.get(f'q{i}', '')
                    }

        # ---------------- TRUE / FALSE ----------------
        elif puzzle_type == 'true_false':
            statements = puzzle_data.get('statements', [])
            total_questions = len(statements)

            for i, statement in enumerate(statements):
                user_answer = answers.get(f'q{i}')
                correct_raw = statement.get('answer')

                correct_bool = str(correct_raw).lower() in ['true', '1', 'yes']
                user_bool = str(user_answer).lower() in ['true', '1', 'yes']

                if user_bool == correct_bool:
                    score += 1
                    results[f'q{i}'] = {
                        'correct': True, 
                        'correct_answer': 'True' if correct_bool else 'False',
                        'student_answer': 'True' if user_bool else 'False'
                    }
                else:
                    results[f'q{i}'] = {
                        'correct': False, 
                        'correct_answer': 'True' if correct_bool else 'False',
                        'student_answer': 'True' if user_bool else 'False'
                    }

        # ---------------- FILL IN THE BLANK (FIXED - MATCHES FRONTEND) ----------------
        elif puzzle_type == 'fill_blank':
            blanks = puzzle_data.get('blanks', [])
            total_questions = len(blanks)  # Each blank sentence is one question
            
            print(f"DEBUG: Processing {len(blanks)} blanks")
            print(f"DEBUG: Received answers: {answers}")

            for i, blank in enumerate(blanks):
                sentence = blank.get('sentence', '')
                correct_answers = blank.get('answers', [])
                
                # Count how many blanks in this sentence
                blank_count = sentence.count('_____')
                print(f"DEBUG: Blank {i} has {blank_count} blanks in sentence: {sentence}")
                print(f"DEBUG: Correct answers for blank {i}: {correct_answers}")
                
                # Check if correct_answers is a list or single string
                if isinstance(correct_answers, str):
                    correct_answers = [correct_answers]
                
                # Get all student answers for this blank
                blank_correct = True
                blank_results = {}
                
                for j in range(blank_count):
                    # Try both key formats: blank_i_j (from current frontend) and q_i (from old format)
                    answer_key = f'blank_{i}_{j}'
                    if answer_key not in answers:
                        # Try old format
                        answer_key = f'q{i}'
                    
                    user_answer_raw = answers.get(answer_key, '')
                    user_answer = str(user_answer_raw).strip().lower()
                    
                    # Get correct answer for this part
                    if j < len(correct_answers):
                        correct_answer_raw = correct_answers[j]
                        correct_answer = str(correct_answer_raw).strip().lower()
                    else:
                        # If there are fewer correct answers than blanks, use the first one
                        correct_answer_raw = correct_answers[0] if correct_answers else ""
                        correct_answer = str(correct_answer_raw).strip().lower()
                    
                    print(f"DEBUG: Blank {i}, part {j}: User='{user_answer}', Correct='{correct_answer}'")
                    
                    # Check if answer is correct (exact match)
                    is_correct = user_answer == correct_answer
                    
                    if not is_correct:
                        blank_correct = False
                    
                    # Store part result
                    blank_results[f'part_{j}'] = {
                        'correct': is_correct,
                        'student_answer': user_answer_raw,
                        'correct_answer': correct_answer_raw
                    }
                
                # If all parts are correct, give point for this blank
                if blank_correct:
                    score += 1
                    print(f"DEBUG: Blank {i} is CORRECT")
                else:
                    print(f"DEBUG: Blank {i} is INCORRECT")
                
                # Store overall blank result
                results[f'blank_{i}'] = {
                    'correct': blank_correct,
                    'parts': blank_results,
                    'sentence': sentence,
                    'correct_answers': correct_answers
                }

        # ---------------- WORD SEARCH ----------------
        elif puzzle_type == 'word_search':
            words = puzzle_data.get('words', [])
            total_questions = len(words)

            for i, word in enumerate(words):
                user_found = answers.get(f'word_{i}', False)

                if user_found:
                    score += 1
                    results[f'word_{i}'] = {
                        'correct': True, 
                        'word': word,
                        'student_answer': 'Found'
                    }
                else:
                    results[f'word_{i}'] = {
                        'correct': False, 
                        'word': word,
                        'student_answer': 'Not found'
                    }

        # ---------------- CALCULATE SCORE ----------------
        print(f"DEBUG: Score={score}, Total={total_questions}")
        percentage = (score / total_questions) * 100 if total_questions > 0 else 0
        required_score = puzzle.get('required_score', 70)
        passed = percentage >= required_score

        # Save progress
        cur.execute("""
            SELECT * FROM student_puzzle_progress
            WHERE student_id = %s AND puzzle_id = %s
        """, (student_id, puzzle_id))
        existing_progress = cur.fetchone()

        if existing_progress:
            cur.execute("""
                UPDATE student_puzzle_progress
                SET attempts = attempts + 1,
                    best_score = GREATEST(best_score, %s),
                    completed = %s,
                    completed_at = CASE WHEN %s = TRUE THEN NOW() ELSE completed_at END
                WHERE student_id = %s AND puzzle_id = %s
            """, (percentage, passed, passed, student_id, puzzle_id))
        else:
            cur.execute("""
                INSERT INTO student_puzzle_progress
                (student_id, puzzle_id, attempts, best_score, completed, completed_at)
                VALUES (%s, %s, 1, %s, %s, %s)
            """, (student_id, puzzle_id, percentage, passed, datetime.now() if passed else None))

        mysql.connection.commit()

        # ---------------- STORY PROGRESS ----------------
        if passed:
            cur.execute("""
                SELECT sp.story_id, sp.page_number
                FROM story_page_puzzles spp
                JOIN story_pages sp ON spp.story_page_id = sp.id
                WHERE spp.id = %s
            """, (puzzle_id,))

            page_info = cur.fetchone()

            if page_info:
                story_id = page_info['story_id']
                current_page = page_info['page_number']

                cur.execute("SELECT COUNT(*) as total FROM story_pages WHERE story_id = %s", (story_id,))
                total_pages = cur.fetchone()['total']

                is_last_page = current_page >= total_pages

                if not is_last_page:
                    cur.execute("""
                        UPDATE student_progress
                        SET current_page = %s
                        WHERE student_id = %s AND story_id = %s
                    """, (current_page + 1, student_id, story_id))
                    mysql.connection.commit()

                return jsonify({
                    'success': True,
                    'passed': True,
                    'score': percentage,
                    'required_score': required_score,
                    'next_page': not is_last_page,
                    'results': results,
                    'message': f'Great! You scored {percentage:.1f}%. Moving to next page...'
                })

        return jsonify({
            'success': True,
            'passed': passed,
            'score': percentage,
            'required_score': required_score,
            'results': results,
            'message': f'You scored {percentage:.1f}%. Need {required_score}% to pass.' if not passed
                       else f'Great! You scored {percentage:.1f}%.'
        })

    except Exception as e:
        print("ERROR submit_puzzle_answer:", e)
        return jsonify({'success': False, 'error': str(e)})

    finally:
        try:
            cur.close()
        except:
            pass

# main 
# API to submit puzzle answer
# @app.route('/api/submit_puzzle_answer', methods=['POST'])
# @student_required
# def submit_puzzle_answer():
#     try:
#         data = request.json
#         puzzle_id = data.get('puzzle_id')
#         answers = data.get('answers', {})

#         if not puzzle_id:
#             return jsonify({'success': False, 'error': 'Puzzle ID required'})

#         cur = mysql.connection.cursor()

#         # Get puzzle data
#         cur.execute("""
#             SELECT spp.*, pt.name as puzzle_type
#             FROM story_page_puzzles spp
#             JOIN puzzle_types pt ON spp.puzzle_type_id = pt.id
#             WHERE spp.id = %s
#         """, (puzzle_id,))

#         puzzle = cur.fetchone()

#         if not puzzle:
#             return jsonify({'success': False, 'error': 'Puzzle not found'})

#         # Get student ID
#         cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
#         student = cur.fetchone()
#         student_id = student['id']

#         puzzle_data = json.loads(puzzle['puzzle_data'])
#         puzzle_type = puzzle['puzzle_type']

#         score = 0
#         total_questions = 0
#         results = {}

#         # ---------------- MULTIPLE CHOICE ----------------
#         if puzzle_type == 'multiple_choice':
#             questions = puzzle_data.get('questions', [])
#             total_questions = len(questions)

#             for i, question in enumerate(questions):
#                 user_answer = answers.get(f'q{i}', '').strip().lower()
#                 correct_answer = question.get('correct_answer', '').strip().lower()

#                 if user_answer == correct_answer:
#                     score += 1
#                     results[f'q{i}'] = {'correct': True, 'correct_answer': question.get('correct_answer')}
#                 else:
#                     results[f'q{i}'] = {'correct': False, 'correct_answer': question.get('correct_answer')}

#         # ---------------- TRUE / FALSE (FIXED) ----------------
#         elif puzzle_type == 'true_false':
#             statements = puzzle_data.get('statements', [])
#             total_questions = len(statements)

#             for i, statement in enumerate(statements):
#                 user_answer = answers.get(f'q{i}')

#                 # Normalize correct answer (handle bool OR string)
#                 correct_raw = statement.get('answer')

#                 if isinstance(correct_raw, bool):
#                     correct_bool = correct_raw
#                 else:
#                     correct_bool = str(correct_raw).lower() in ['true', '1', 'yes']

#                 # Normalize user answer
#                 if user_answer is None:
#                     user_bool = None
#                 else:
#                     user_bool = str(user_answer).lower() in ['true', '1', 'yes']

#                 if user_bool is not None and user_bool == correct_bool:
#                     score += 1
#                     results[f'q{i}'] = {
#                         'correct': True,
#                         'correct_answer': 'True' if correct_bool else 'False'
#                     }
#                 else:
#                     results[f'q{i}'] = {
#                         'correct': False,
#                         'correct_answer': 'True' if correct_bool else 'False'
#                     }

#         # ---------------- FILL IN THE BLANK ----------------
#         elif puzzle_type == 'fill_blank':
#             blanks = puzzle_data.get('blanks', [])
#             total_questions = len(blanks)

#             for i, blank in enumerate(blanks):
#                 user_answer = answers.get(f'q{i}', '').strip().lower()
#                 correct_answers = [ans.strip().lower() for ans in blank.get('answers', [])]

#                 if user_answer in correct_answers:
#                     score += 1
#                     results[f'q{i}'] = {'correct': True, 'correct_answer': blank['answers'][0]}
#                 else:
#                     results[f'q{i}'] = {'correct': False, 'correct_answer': blank['answers'][0]}

#         # ---------------- WORD SEARCH ----------------
#         elif puzzle_type == 'word_search':
#             words = puzzle_data.get('words', [])
#             total_questions = len(words)

#             for i, word in enumerate(words):
#                 user_found = answers.get(f'word_{i}', False)

#                 if user_found:
#                     score += 1
#                     results[f'word_{i}'] = {'correct': True, 'word': word}
#                 else:
#                     results[f'word_{i}'] = {'correct': False, 'word': word}

#         # ---------------- CALCULATE SCORE ----------------
#         percentage = (score / total_questions) * 100 if total_questions > 0 else 0
#         required_score = puzzle.get('required_score', 70)
#         passed = percentage >= required_score

#         # Get existing progress
#         cur.execute("""
#             SELECT * FROM student_puzzle_progress
#             WHERE student_id = %s AND puzzle_id = %s
#         """, (student_id, puzzle_id))

#         existing_progress = cur.fetchone()

#         if existing_progress:
#             cur.execute("""
#                 UPDATE student_puzzle_progress
#                 SET attempts = attempts + 1,
#                     best_score = GREATEST(best_score, %s),
#                     completed = %s,
#                     completed_at = CASE WHEN %s = TRUE THEN NOW() ELSE completed_at END
#                 WHERE student_id = %s AND puzzle_id = %s
#             """, (percentage, passed, passed, student_id, puzzle_id))
#         else:
#             cur.execute("""
#                 INSERT INTO student_puzzle_progress
#                 (student_id, puzzle_id, attempts, best_score, completed, completed_at)
#                 VALUES (%s, %s, 1, %s, %s, %s)
#             """, (student_id, puzzle_id, percentage, passed, datetime.now() if passed else None))

#         mysql.connection.commit()

#         # ---------------- STORY PROGRESS ----------------
#         if passed:
#             cur.execute("""
#                 SELECT sp.story_id, sp.page_number
#                 FROM story_page_puzzles spp
#                 JOIN story_pages sp ON spp.story_page_id = sp.id
#                 WHERE spp.id = %s
#             """, (puzzle_id,))

#             page_info = cur.fetchone()

#             if page_info:
#                 story_id = page_info['story_id']
#                 current_page = page_info['page_number']

#                 cur.execute("SELECT COUNT(*) as total FROM story_pages WHERE story_id = %s", (story_id,))
#                 total_pages = cur.fetchone()['total']

#                 is_last_page = current_page >= total_pages

#                 if not is_last_page:
#                     cur.execute("""
#                         UPDATE student_progress
#                         SET current_page = %s
#                         WHERE student_id = %s AND story_id = %s
#                     """, (current_page + 1, student_id, story_id))
#                     mysql.connection.commit()

#                 return jsonify({
#                     'success': True,
#                     'passed': True,
#                     'score': percentage,
#                     'required_score': required_score,
#                     'next_page': not is_last_page,
#                     'results': results,
#                     'message': f'Great! You scored {percentage:.1f}%. Moving to next page...'
#                 })

#         return jsonify({
#             'success': True,
#             'passed': passed,
#             'score': percentage,
#             'required_score': required_score,
#             'results': results,
#             'message': f'You scored {percentage:.1f}%. Need {required_score}% to pass. Try again!'
#         })

#     except Exception as e:
#         print("ERROR submit_puzzle_answer:", e)
#         return jsonify({'success': False, 'error': str(e)})

#     finally:
#         try:
#             cur.close()
#         except:
#             pass

# API to skip puzzle (limited attempts)
@app.route('/api/skip_puzzle', methods=['POST'])
@student_required
def skip_puzzle():
    try:
        data = request.json
        puzzle_id = data.get('puzzle_id')
        
        cur = mysql.connection.cursor()
        
        # Get student ID
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        student_id = student['id']
        
        # Get story page info
        cur.execute("""
            SELECT sp.story_id, sp.page_number
            FROM story_page_puzzles spp
            JOIN story_pages sp ON spp.story_page_id = sp.id
            WHERE spp.id = %s
        """, (puzzle_id,))
        
        page_info = cur.fetchone()
        
        if not page_info:
            return jsonify({'success': False, 'error': 'Page not found'})
        
        story_id = page_info['story_id']
        current_page = page_info['page_number']
        
        # Get total pages
        cur.execute("SELECT COUNT(*) as total FROM story_pages WHERE story_id = %s", (story_id,))
        total_pages = cur.fetchone()['total']
        
        # Check if this is the last page
        is_last_page = current_page >= total_pages
        
        if not is_last_page:
            # Update to next page
            cur.execute("""
                UPDATE student_progress
                SET current_page = %s
                WHERE student_id = %s AND story_id = %s
            """, (current_page + 1, student_id, story_id))
            mysql.connection.commit()
            
            # Mark puzzle as skipped (not completed)
            cur.execute("""
                INSERT IGNORE INTO student_puzzle_progress
                (student_id, puzzle_id, attempts, best_score, completed)
                VALUES (%s, %s, 1, 0, FALSE)
                ON DUPLICATE KEY UPDATE attempts = attempts + 1
            """, (student_id, puzzle_id))
            mysql.connection.commit()
        
        return jsonify({
            'success': True,
            'next_page': not is_last_page,
            'message': 'Puzzle skipped. Moving to next page.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# @app.route('/api/create_puzzle', methods=['POST'])
# @teacher_required
# def create_puzzle():
#     try:
#         data = request.json
#         page_id = data.get('page_id')
#         puzzle_type = data.get('puzzle_type')
#         difficulty = data.get('difficulty', 'medium')
#         time_limit = data.get('time_limit', 180)
#         required_score = data.get('required_score', 70)
        
#         cur = mysql.connection.cursor()
        
#         # Get page details
#         cur.execute("SELECT * FROM story_pages WHERE id = %s", (page_id,))
#         page = cur.fetchone()
        
#         if not page:
#             return jsonify({'success': False, 'error': 'Page not found'})
        
#         # Get puzzle type ID
#         cur.execute("SELECT id FROM puzzle_types WHERE name = %s", (puzzle_type,))
#         puzzle_type_data = cur.fetchone()
        
#         if not puzzle_type_data:
#             return jsonify({'success': False, 'error': 'Invalid puzzle type'})
        
#         puzzle_type_id = puzzle_type_data['id']
        
#         # Generate puzzle data based on page content and puzzle type
#         puzzle_data = generate_puzzle_from_text(page['text_content'], puzzle_type)
        
#         # Save puzzle to database
#         cur.execute("""
#             INSERT INTO story_page_puzzles 
#             (story_page_id, puzzle_type_id, puzzle_data, difficulty, time_limit, required_score)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             ON DUPLICATE KEY UPDATE 
#             puzzle_data = VALUES(puzzle_data),
#             difficulty = VALUES(difficulty),
#             time_limit = VALUES(time_limit),
#             required_score = VALUES(required_score)
#         """, (page_id, puzzle_type_id, json.dumps(puzzle_data), difficulty, time_limit, required_score))
        
#         mysql.connection.commit()
#         cur.close()
        
#         return jsonify({'success': True, 'message': 'Puzzle created successfully'})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)})
@app.route('/api/create_puzzle', methods=['POST'])
@teacher_required
def create_puzzle():
    try:
        data = request.get_json()

        page_id = data.get('page_id')
        puzzle_type = data.get('puzzle_type')
        difficulty = data.get('difficulty', 'medium')
        time_limit = int(data.get('time_limit', 180))
        required_score = int(data.get('required_score', 70))

        if not page_id or not puzzle_type:
            return jsonify({'success': False, 'error': 'Missing page or puzzle type'})

        cur = mysql.connection.cursor()

        # 1️⃣ Get page details
        cur.execute("SELECT * FROM story_pages WHERE id = %s", (page_id,))
        page = cur.fetchone()

        if not page:
            cur.close()
            return jsonify({'success': False, 'error': 'Page not found'})

        # 2️⃣ Get puzzle type ID
        cur.execute("SELECT id FROM puzzle_types WHERE name = %s", (puzzle_type,))
        puzzle_type_data = cur.fetchone()

        if not puzzle_type_data:
            cur.close()
            return jsonify({'success': False, 'error': 'Invalid puzzle type'})

        puzzle_type_id = puzzle_type_data['id']

        # 3️⃣ Generate puzzle from text
        puzzle_data_obj = generate_puzzle_from_text(page['text_content'], puzzle_type)

        # IMPORTANT: Convert to JSON string for DB
        puzzle_data_json = json.dumps(puzzle_data_obj)

        # 4️⃣ Check if puzzle already exists for this page
        cur.execute("""
            SELECT id FROM story_page_puzzles 
            WHERE story_page_id = %s
        """, (page_id,))
        existing = cur.fetchone()

        if existing:
            # 5️⃣ Update existing puzzle
            cur.execute("""
                UPDATE story_page_puzzles
                SET puzzle_type_id = %s,
                    puzzle_data = %s,
                    difficulty = %s,
                    time_limit = %s,
                    required_score = %s
                WHERE story_page_id = %s
            """, (
                puzzle_type_id,
                puzzle_data_json,
                difficulty,
                time_limit,
                required_score,
                page_id
            ))
        else:
            # 6️⃣ Insert new puzzle
            cur.execute("""
                INSERT INTO story_page_puzzles
                (story_page_id, puzzle_type_id, puzzle_data, difficulty, time_limit, required_score)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                page_id,
                puzzle_type_id,
                puzzle_data_json,
                difficulty,
                time_limit,
                required_score
            ))

        # 7️⃣ COMMIT (VERY IMPORTANT)
        mysql.connection.commit()
        cur.close()

        return jsonify({'success': True})

    except Exception as e:
        print("CREATE PUZZLE ERROR:", str(e))
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/api/auto_generate_puzzle', methods=['POST'])
@teacher_required
def auto_generate_puzzle():
    try:
        data = request.json
        page_id = data.get('page_id')
        
        cur = mysql.connection.cursor()
        
        # Get page details
        cur.execute("SELECT * FROM story_pages WHERE id = %s", (page_id,))
        page = cur.fetchone()
        
        if not page:
            return jsonify({'success': False, 'error': 'Page not found'})
        
        # Choose random puzzle type based on text length
        text_length = len(page['text_content'])
        
        if text_length > 200:
            puzzle_types = ['word_search', 'fill_blank', 'multiple_choice']
        elif text_length > 100:
            puzzle_types = ['true_false', 'multiple_choice', 'fill_blank']
        else:
            puzzle_types = ['true_false', 'multiple_choice']
        
        selected_type = random.choice(puzzle_types)
        
        # Get puzzle type ID
        cur.execute("SELECT id FROM puzzle_types WHERE name = %s", (selected_type,))
        puzzle_type_data = cur.fetchone()
        
        if not puzzle_type_data:
            return jsonify({'success': False, 'error': 'Invalid puzzle type'})
        
        puzzle_type_id = puzzle_type_data['id']
        
        # Generate puzzle from text content
        puzzle_data = generate_puzzle_from_text(page['text_content'], selected_type)
        
        # Save puzzle to database
        cur.execute("""
            INSERT INTO story_page_puzzles 
            (story_page_id, puzzle_type_id, puzzle_data, difficulty, time_limit, required_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            puzzle_data = VALUES(puzzle_data),
            difficulty = VALUES(difficulty),
            time_limit = VALUES(time_limit),
            required_score = VALUES(required_score)
        """, (page_id, puzzle_type_id, json.dumps(puzzle_data), 'medium', 180, 70))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': f'Puzzle ({selected_type}) generated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_puzzle', methods=['POST'])
@teacher_required
def delete_puzzle():
    try:
        data = request.json
        puzzle_id = data.get('puzzle_id')
        
        cur = mysql.connection.cursor()
        
        # Delete puzzle
        cur.execute("DELETE FROM story_page_puzzles WHERE id = %s", (puzzle_id,))
        
        # Also delete student progress for this puzzle
        cur.execute("DELETE FROM student_puzzle_progress WHERE puzzle_id = %s", (puzzle_id,))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Puzzle deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/teacher/preview_puzzle/<int:puzzle_id>')
@teacher_required
def preview_puzzle(puzzle_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get puzzle details with story_id
        cur.execute("""
            SELECT spp.*, pt.name as puzzle_type_name, sp.page_number, sp.story_id
            FROM story_page_puzzles spp
            JOIN puzzle_types pt ON spp.puzzle_type_id = pt.id
            JOIN story_pages sp ON spp.story_page_id = sp.id
            WHERE spp.id = %s
        """, (puzzle_id,))
        
        puzzle = cur.fetchone()
        
        if not puzzle:
            flash('Puzzle not found', 'danger')
            return redirect(url_for('teacher_stories'))
        
        # Parse puzzle data if it's a JSON string
        if isinstance(puzzle['puzzle_data'], str):
            try:
                puzzle_data = json.loads(puzzle['puzzle_data'])
                puzzle['puzzle_data'] = puzzle_data
            except json.JSONDecodeError:
                puzzle['puzzle_data'] = {}
        elif puzzle['puzzle_data'] is None:
            puzzle['puzzle_data'] = {}
        
        cur.close()
        
        return render_template('teacher/puzzle_preview.html', 
                             puzzle=puzzle,
                             story_id=puzzle.get('story_id'))
    except Exception as e:
        flash(f'Error loading puzzle: {str(e)}', 'danger')
        return redirect(url_for('teacher_stories'))

# Custom Jinja2 filter to convert numbers to letters
@app.template_filter('to_letters')
def to_letters_filter(num):
    """Convert number to letter (1 -> A, 2 -> B, etc.)"""
    if not isinstance(num, int):
        try:
            num = int(num)
        except (ValueError, TypeError):
            return str(num)
    
    if 1 <= num <= 26:
        return chr(64 + num)  # 65 is 'A' in ASCII
    elif 27 <= num <= 52:
        return f"A{chr(64 + num - 26)}"  # For numbers beyond 26
    else:
        return str(num)

# Or a simpler version
@app.template_filter('to_letters')
def to_letters_filter(num):
    """Convert number to letter (1 -> A, 2 -> B, etc.)"""
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    
    if isinstance(num, int) and 1 <= num <= len(letters):
        return letters[num - 1]
    elif isinstance(num, str) and num.isdigit():
        num_int = int(num)
        if 1 <= num_int <= len(letters):
            return letters[num_int - 1]
    
    return str(num)


# ======================  Student Portal Routes ==================================================
# main code 
# @app.route('/student/dashboard')
# @student_required
# def student_dashboard():
#     try:
#         cur = mysql.connection.cursor()
        
#         # Get student details
#         cur.execute("""
#             SELECT s.* FROM students s
#             JOIN users u ON s.user_id = u.id
#             WHERE u.id = %s
#         """, (session['user_id'],))
#         student = cur.fetchone()
        
#         if not student:
#             flash('Student not found', 'danger')
#             return redirect(url_for('logout'))
        
#         # Get assigned stories with quiz attempt status
#         cur.execute("""
#             SELECT s.*, t.first_name as teacher_first_name, t.last_name as teacher_last_name,
#                    sp.current_page, sp.is_completed,
#                    (SELECT COUNT(*) FROM story_pages sp2 WHERE sp2.story_id = s.id) as total_pages,
#                    (SELECT COUNT(*) FROM quizzes q WHERE q.story_id = s.id) as has_quiz,
#                    (SELECT COUNT(*) FROM student_quiz_attempts sqa 
#                     JOIN quizzes q ON sqa.quiz_id = q.id 
#                     WHERE q.story_id = s.id AND sqa.student_id = %s) as quiz_attempted
#             FROM stories s
#             JOIN teachers t ON s.teacher_id = t.id
#             JOIN class_assignments ca ON s.id = ca.story_id AND ca.class_level = %s
#             LEFT JOIN student_progress sp ON s.id = sp.story_id AND sp.student_id = %s
#             WHERE s.is_published = TRUE
#             ORDER BY s.created_at DESC
#         """, (student['id'], student['class_level'], student['id']))
        
#         stories = cur.fetchall()
#         cur.close()
        
#         return render_template('student/dashboard.html', student=student, stories=stories)
#     except Exception as e:
#         flash(f'Error loading dashboard: {str(e)}', 'danger')
#         return redirect(url_for('logout'))

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    try:
        cur = mysql.connection.cursor()
        
        # ===============================
        # Get student details
        # ===============================
        cur.execute("""
            SELECT s.* FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE u.id = %s
        """, (session['user_id'],))
        student = cur.fetchone()
        
        if not student:
            flash('Student not found', 'danger')
            cur.close()
            return redirect(url_for('logout'))
        
        # ===============================
        # Get assigned stories with quiz attempt status
        # ===============================
        cur.execute("""
            SELECT s.*, 
                   t.first_name as teacher_first_name, 
                   t.last_name as teacher_last_name,
                   sp.current_page, 
                   sp.is_completed,
                   (SELECT COUNT(*) 
                    FROM story_pages sp2 
                    WHERE sp2.story_id = s.id) as total_pages,
                   (SELECT COUNT(*) 
                    FROM quizzes q 
                    WHERE q.story_id = s.id) as has_quiz,
                   (SELECT COUNT(*) 
                    FROM student_quiz_attempts sqa 
                    JOIN quizzes q ON sqa.quiz_id = q.id 
                    WHERE q.story_id = s.id 
                      AND sqa.student_id = %s) as quiz_attempted
            FROM stories s
            JOIN teachers t ON s.teacher_id = t.id
            JOIN class_assignments ca 
                 ON s.id = ca.story_id 
                AND ca.class_level = %s
            LEFT JOIN student_progress sp 
                   ON s.id = sp.story_id 
                  AND sp.student_id = %s
            WHERE s.is_published = TRUE
            ORDER BY s.created_at DESC
        """, (student['id'], student['class_level'], student['id']))
        
        stories = cur.fetchall()

        # ===============================
        # 🔥 CHAT: Find teacher for this class
        # ===============================
        cur.execute("""
            SELECT t.id as teacher_id
            FROM class_assignments ca
            JOIN stories s ON s.id = ca.story_id
            JOIN teachers t ON t.id = s.teacher_id
            WHERE ca.class_level = %s
            LIMIT 1
        """, (student['class_level'],))
        
        teacher = cur.fetchone()

        conversation_id = None
        if teacher:
            conversation_id = get_or_create_conversation(
                teacher['teacher_id'], 
                student['id']
            )
            # Get unread count for student
            cur.execute("""
                SELECT COUNT(*) as unread_count
                FROM chat_messages cm
                WHERE cm.conversation_id = %s 
                  AND cm.sender_type = 'teacher'
                  AND cm.is_read = FALSE
            """, (conversation_id,))
            
            unread_result = cur.fetchone()
            unread_count = unread_result['unread_count'] if unread_result else 0   

        cur.close()
        
        # ===============================
        # Render dashboard WITH chat
        # ===============================
        return render_template(
            'student/dashboard.html',
            student=student,
            stories=stories,
            conversation_id=conversation_id,
            unread_count=unread_count 
        )

    except Exception as e:
        try:
            cur.close()
        except:
            pass
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('logout'))


# # main
# @app.route('/student/story/<int:story_id>')
# @student_required
# def view_story(story_id):
#     try:
#         cur = mysql.connection.cursor()
        
#         # Get story details
#         cur.execute("""
#             SELECT s.*, t.first_name as teacher_first_name, t.last_name as teacher_last_name
#             FROM stories s
#             JOIN teachers t ON s.teacher_id = t.id
#             WHERE s.id = %s AND s.is_published = TRUE
#         """, (story_id,))
#         story = cur.fetchone()
        
#         if not story:
#             flash('Story not found', 'danger')
#             return redirect(url_for('student_dashboard'))
        
#         # Get story pages
#         cur.execute("""
#             SELECT * FROM story_pages
#             WHERE story_id = %s
#             ORDER BY page_number
#         """, (story_id,))
#         pages = cur.fetchall()
        
#         # Get student ID
#         cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
#         student = cur.fetchone()
        
#         # Get or create student progress
#         cur.execute("""
#             SELECT * FROM student_progress
#             WHERE student_id = %s AND story_id = %s
#         """, (student['id'], story_id))
        
#         progress = cur.fetchone()
        
#         total_pages = len(pages)
        
#         if not progress:
#             # Create new progress entry
#             cur.execute("""
#                 INSERT INTO student_progress 
#                 (student_id, story_id, current_page, started_at, is_completed)
#                 VALUES (%s, %s, 1, NOW(), FALSE)
#             """, (student['id'], story_id))
#             mysql.connection.commit()
            
#             # Get the newly created progress
#             cur.execute("""
#                 SELECT * FROM student_progress
#                 WHERE student_id = %s AND story_id = %s
#             """, (student['id'], story_id))
#             progress = cur.fetchone()
#         else:
#             # Check if story should be marked as completed
#             if progress['current_page'] >= total_pages and not progress['is_completed']:
#                 cur.execute("""
#                     UPDATE student_progress 
#                     SET is_completed = TRUE, completed_at = NOW()
#                     WHERE student_id = %s AND story_id = %s
#                 """, (student['id'], story_id))
#                 mysql.connection.commit()
                
#                 # Refresh progress data
#                 cur.execute("""
#                     SELECT * FROM student_progress
#                     WHERE student_id = %s AND story_id = %s
#                 """, (student['id'], story_id))
#                 progress = cur.fetchone()
        
#         cur.close()
        
#         return render_template('student/story_view.html', 
#                              story=story, 
#                              pages=pages, 
#                              progress=progress,
#                              total_pages=total_pages)
#     except Exception as e:
#         flash(f'Error loading story: {str(e)}', 'danger')
#         return redirect(url_for('student_dashboard'))
# Updated student story view route with puzzles
@app.route('/student/story/<int:story_id>')
@student_required
def view_story(story_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get story details
        cur.execute("""
            SELECT s.*, t.first_name as teacher_first_name, t.last_name as teacher_last_name
            FROM stories s
            JOIN teachers t ON s.teacher_id = t.id
            WHERE s.id = %s AND s.is_published = TRUE
        """, (story_id,))
        story = cur.fetchone()
        
        if not story:
            flash('Story not found', 'danger')
            return redirect(url_for('student_dashboard'))
        
        # Get story pages
        cur.execute("""
            SELECT * FROM story_pages
            WHERE story_id = %s
            ORDER BY page_number
        """, (story_id,))
        pages = cur.fetchall()
        
        # Get student ID
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        student_id = student['id']
        
        # Get or create student progress
        cur.execute("""
            SELECT * FROM student_progress
            WHERE student_id = %s AND story_id = %s
        """, (student_id, story_id))
        
        progress = cur.fetchone()
        
        total_pages = len(pages)
        
        if not progress:
            # Create new progress entry
            cur.execute("""
                INSERT INTO student_progress 
                (student_id, story_id, current_page, started_at, is_completed)
                VALUES (%s, %s, 1, NOW(), FALSE)
            """, (student_id, story_id))
            mysql.connection.commit()
            
            cur.execute("""
                SELECT * FROM student_progress
                WHERE student_id = %s AND story_id = %s
            """, (student_id, story_id))
            progress = cur.fetchone()
        
        current_page = progress['current_page']
        current_page_data = pages[current_page - 1]
        
        # Check if puzzle exists for this page, if not create one
        cur.execute("""
            SELECT spp.*, pt.name as puzzle_type_name
            FROM story_page_puzzles spp
            JOIN puzzle_types pt ON spp.puzzle_type_id = pt.id
            WHERE spp.story_page_id = %s
        """, (current_page_data['id'],))
        
        puzzle = cur.fetchone()
        
        # If no puzzle exists for this page, create one automatically
        if not puzzle and current_page_data['text_content']:
            # Choose a random puzzle type based on text length
            text_length = len(current_page_data['text_content'])
            
            if text_length > 200:
                puzzle_types = ['word_search', 'fill_blank', 'multiple_choice']
            elif text_length > 100:
                puzzle_types = ['true_false', 'multiple_choice', 'fill_blank']
            else:
                puzzle_types = ['true_false', 'multiple_choice']
            
            selected_type = random.choice(puzzle_types)
            
            # Get puzzle type ID
            cur.execute("SELECT id FROM puzzle_types WHERE name = %s", (selected_type,))
            puzzle_type = cur.fetchone()
            
            if puzzle_type:
                # Generate puzzle from text content
                puzzle_data = generate_puzzle_from_text(
                    current_page_data['text_content'], 
                    selected_type
                )
                
                # Save puzzle to database
                cur.execute("""
                    INSERT INTO story_page_puzzles 
                    (story_page_id, puzzle_type_id, puzzle_data, difficulty, time_limit, required_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    current_page_data['id'],
                    puzzle_type['id'],
                    json.dumps(puzzle_data),
                    'medium',
                    180,
                    70
                ))
                mysql.connection.commit()
                
                # Get the newly created puzzle
                cur.execute("""
                    SELECT spp.*, pt.name as puzzle_type_name
                    FROM story_page_puzzles spp
                    JOIN puzzle_types pt ON spp.puzzle_type_id = pt.id
                    WHERE spp.story_page_id = %s
                """, (current_page_data['id'],))
                puzzle = cur.fetchone()
        
        # Get student's puzzle progress for this page
        student_puzzle_progress = None
        if puzzle:
            cur.execute("""
                SELECT * FROM student_puzzle_progress
                WHERE student_id = %s AND puzzle_id = %s
            """, (student_id, puzzle['id']))
            student_puzzle_progress = cur.fetchone()
        
        cur.close()
        
        return render_template('student/story_view.html', 
                             story=story, 
                             pages=pages, 
                             progress=progress,
                             total_pages=total_pages,
                             current_page_data=current_page_data,
                             puzzle=puzzle,
                             student_puzzle_progress=student_puzzle_progress)
    except Exception as e:
        flash(f'Error loading story: {str(e)}', 'danger')
        return redirect(url_for('student_dashboard'))
      
# @app.route('/api/update_progress', methods=['POST'])
# @student_required
# def update_progress():
#     try:
#         data = request.json
#         story_id = data.get('story_id')
#         current_page = data.get('current_page')
        
#         cur = mysql.connection.cursor()
        
#         # Get student ID
#         cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
#         student = cur.fetchone()
        
#         # Get total pages in the story
#         cur.execute("SELECT COUNT(*) as total_pages FROM story_pages WHERE story_id = %s", (story_id,))
#         total_pages_result = cur.fetchone()
#         total_pages = total_pages_result['total_pages'] if total_pages_result else 0
        
#         # Check if this is the last page
#         is_completed = current_page >= total_pages
        
#         if is_completed:
#             # Mark as completed
#             cur.execute("""
#                 UPDATE student_progress 
#                 SET current_page = %s, 
#                     is_completed = TRUE, 
#                     completed_at = COALESCE(completed_at, NOW())
#                 WHERE student_id = %s AND story_id = %s
#             """, (current_page, student['id'], story_id))
            
#             # If no rows affected, insert new record
#             if cur.rowcount == 0:
#                 cur.execute("""
#                     INSERT INTO student_progress 
#                     (student_id, story_id, current_page, is_completed, started_at, completed_at)
#                     VALUES (%s, %s, %s, TRUE, NOW(), NOW())
#                 """, (student['id'], story_id, current_page))
#         else:
#             # Update current page without marking as completed
#             cur.execute("""
#                 INSERT INTO student_progress 
#                 (student_id, story_id, current_page, is_completed, started_at)
#                 VALUES (%s, %s, %s, FALSE, NOW())
#                 ON DUPLICATE KEY UPDATE 
#                 current_page = VALUES(current_page),
#                 is_completed = CASE 
#                     WHEN VALUES(current_page) >= %s THEN TRUE 
#                     ELSE is_completed 
#                 END,
#                 completed_at = CASE 
#                     WHEN VALUES(current_page) >= %s THEN COALESCE(completed_at, NOW())
#                     ELSE completed_at 
#                 END
#             """, (student['id'], story_id, current_page, total_pages, total_pages))
        
#         mysql.connection.commit()
#         cur.close()
        
#         return jsonify({
#             'success': True, 
#             'is_completed': is_completed,
#             'total_pages': total_pages
#         })
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/update_progress', methods=['POST'])
@student_required
def update_progress():
    try:
        data = request.json
        story_id = data.get('story_id')
        current_page = data.get('current_page')
        
        if not story_id or not current_page:
            return jsonify({'success': False, 'error': 'Missing story_id or current_page'}), 400
        
        cur = mysql.connection.cursor()
        
        # Get student ID
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student_result = cur.fetchone()
        
        if not student_result:
            cur.close()
            return jsonify({'success': False, 'error': 'Student not found'}), 404
        
        student_id = student_result['id']
        
        # Get total pages in the story
        cur.execute("SELECT COUNT(*) as total_pages FROM story_pages WHERE story_id = %s", (story_id,))
        total_pages_result = cur.fetchone()
        total_pages = total_pages_result['total_pages'] if total_pages_result and total_pages_result['total_pages'] else 0
        
        # Ensure current_page doesn't exceed total_pages
        if current_page > total_pages:
            current_page = total_pages
        
        # Check if this is the last page
        is_completed = current_page >= total_pages
        
        # Check if progress entry already exists
        cur.execute("SELECT * FROM student_progress WHERE student_id = %s AND story_id = %s", 
                   (student_id, story_id))
        existing_progress = cur.fetchone()
        
        if existing_progress:
            # Update existing progress
            if is_completed and not existing_progress['is_completed']:
                # Story just completed - set completed_at
                cur.execute("""
                    UPDATE student_progress 
                    SET current_page = %s, 
                        is_completed = TRUE,
                        completed_at = NOW()
                    WHERE student_id = %s AND story_id = %s
                """, (current_page, student_id, story_id))
            else:
                # Just updating page, not completing
                cur.execute("""
                    UPDATE student_progress 
                    SET current_page = %s
                    WHERE student_id = %s AND story_id = %s
                """, (current_page, student_id, story_id))
        else:
            # Insert new progress entry
            if is_completed:
                # Story completed in first go
                cur.execute("""
                    INSERT INTO student_progress 
                    (student_id, story_id, current_page, is_completed, started_at, completed_at)
                    VALUES (%s, %s, %s, TRUE, NOW(), NOW())
                """, (student_id, story_id, current_page))
            else:
                # Story not completed yet
                cur.execute("""
                    INSERT INTO student_progress 
                    (student_id, story_id, current_page, is_completed, started_at)
                    VALUES (%s, %s, %s, FALSE, NOW())
                """, (student_id, story_id, current_page))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            'success': True, 
            'is_completed': is_completed,
            'total_pages': total_pages,
            'current_page': current_page
        })
    except Exception as e:
        app.logger.error(f"Error updating progress: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
          
# @app.route('/student/quiz/<int:story_id>', methods=['GET', 'POST'])
# @student_required
# def take_quiz(story_id):
#     try:
#         cur = mysql.connection.cursor()
        
#         # Get student ID
#         cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
#         student = cur.fetchone()
        
#         # Check if student has already attempted this quiz
#         cur.execute("""
#             SELECT sqa.*, q.title as quiz_title
#             FROM student_quiz_attempts sqa
#             JOIN quizzes q ON sqa.quiz_id = q.id
#             WHERE q.story_id = %s AND sqa.student_id = %s
#             ORDER BY sqa.submitted_at DESC
#             LIMIT 1
#         """, (story_id, student['id']))
        
#         previous_attempt = cur.fetchone()
        
#         if previous_attempt:
#             # Student has already attempted this quiz
#             flash('You have already completed this quiz. You cannot retake it.', 'warning')
            
#             # Get quiz details for display
#             cur.execute("""
#                 SELECT q.*, s.title as story_title
#                 FROM quizzes q
#                 JOIN stories s ON q.story_id = s.id
#                 WHERE q.story_id = %s
#             """, (story_id,))
#             quiz = cur.fetchone()
            
#             # Get previous attempt details
#             cur.execute("""
#                 SELECT sqa.*, qq.question_text, qq.question_type, qq.points,
#                        qq.correct_answer, qq.explanation,
#                        qq.option_a, qq.option_b, qq.option_c, qq.option_d,
#                        sqa2.student_answer, sqa2.is_correct
#                 FROM student_quiz_attempts sqa
#                 JOIN quizzes q ON sqa.quiz_id = q.id
#                 JOIN student_quiz_answers sqa2 ON sqa.id = sqa2.attempt_id
#                 JOIN quiz_questions qq ON sqa2.question_id = qq.id
#                 WHERE sqa.id = %s
#                 ORDER BY qq.id
#             """, (previous_attempt['id'],))
            
#             answers = cur.fetchall()
            
#             cur.close()
            
#             return render_template('student/quiz_result.html', 
#                                  quiz=quiz, 
#                                  score=previous_attempt['score'], 
#                                  passed=previous_attempt['score'] >= quiz['passing_score'],
#                                  total_points=10,  # You may need to adjust this
#                                  earned_points=previous_attempt['score'],
#                                  stats=None,
#                                  answers=answers,
#                                  questions=[],
#                                  is_retake=False)
        
#         # Get quiz details if not attempted before
#         cur.execute("""
#             SELECT q.*, s.title as story_title
#             FROM quizzes q
#             JOIN stories s ON q.story_id = s.id
#             WHERE q.story_id = %s
#         """, (story_id,))
#         quiz = cur.fetchone()
        
#         if not quiz:
#             flash('Quiz not found for this story', 'danger')
#             return redirect(url_for('student_dashboard'))
        
#         # Get quiz questions
#         cur.execute("""
#             SELECT * FROM quiz_questions
#             WHERE quiz_id = %s
#             ORDER BY id
#         """, (quiz['id'],))
#         questions = cur.fetchall()
        
#         if request.method == 'POST':
#             # Calculate score
#             score = 0
#             total_points = 0
#             answers = []
            
#             for question in questions:
#                 total_points += question['points']
#                 student_answer = request.form.get(f'question_{question["id"]}', '')
                
#                 is_correct = False
#                 if question['question_type'] == 'multiple_choice':
#                     is_correct = student_answer == question['correct_answer']
#                 elif question['question_type'] == 'true_false':
#                     is_correct = student_answer.lower() == question['correct_answer'].lower()
#                 else:  # short_answer
#                     is_correct = student_answer.strip().lower() == question['correct_answer'].strip().lower()
                
#                 if is_correct:
#                     score += question['points']
                
#                 answers.append({
#                     'question_id': question['id'],
#                     'student_answer': student_answer,
#                     'is_correct': is_correct,
#                     'correct_answer': question['correct_answer'],
#                     'explanation': question['explanation']
#                 })
            
#             percentage_score = (score / total_points) * 100 if total_points > 0 else 0
            
#             # Record attempt
#             cur.execute("""
#                 INSERT INTO student_quiz_attempts (student_id, quiz_id, score, time_taken)
#                 VALUES (%s, %s, %s, %s)
#             """, (student['id'], quiz['id'], percentage_score, request.form.get('time_taken', 0)))
            
#             attempt_id = cur.lastrowid
            
#             # Record answers
#             for answer in answers:
#                 cur.execute("""
#                     INSERT INTO student_quiz_answers (attempt_id, question_id, student_answer, is_correct)
#                     VALUES (%s, %s, %s, %s)
#                 """, (attempt_id, answer['question_id'], answer['student_answer'], answer['is_correct']))
            
#             mysql.connection.commit()
            
#             # Get statistics
#             cur.execute("""
#                 SELECT 
#                     COUNT(*) as total_attempts,
#                     AVG(score) as average_score,
#                     SUM(CASE WHEN score >= %s THEN 1 ELSE 0 END) as passed_count,
#                     SUM(CASE WHEN score < %s THEN 1 ELSE 0 END) as failed_count
#                 FROM student_quiz_attempts
#                 WHERE quiz_id = %s
#             """, (quiz['passing_score'], quiz['passing_score'], quiz['id']))
            
#             stats = cur.fetchone()
            
#             cur.close()
            
#             return render_template('student/quiz_result.html', 
#                                  quiz=quiz, 
#                                  score=percentage_score, 
#                                  passed=percentage_score >= quiz['passing_score'],
#                                  total_points=total_points,
#                                  earned_points=score,
#                                  stats=stats,
#                                  answers=answers,
#                                  questions=questions,
#                                  is_retake=False)
        
#         cur.close()
#         return render_template('student/quiz.html', quiz=quiz, questions=questions)
#     except Exception as e:
#         flash(f'Error loading quiz: {str(e)}', 'danger')
#         return redirect(url_for('student_dashboard'))

# main
@app.route('/student/quiz/<int:story_id>', methods=['GET', 'POST'])
@student_required
def take_quiz(story_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get student ID
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        
        if not student:
            flash('Student not found', 'danger')
            return redirect(url_for('student_dashboard'))
        
        # Check if student has already attempted this quiz
        cur.execute("""
            SELECT sqa.*, q.title as quiz_title
            FROM student_quiz_attempts sqa
            JOIN quizzes q ON sqa.quiz_id = q.id
            WHERE q.story_id = %s AND sqa.student_id = %s
            ORDER BY sqa.submitted_at DESC
            LIMIT 1
        """, (story_id, student['id']))
        
        previous_attempt = cur.fetchone()
        
        if previous_attempt:
            # Student has already attempted this quiz
            flash('You have already completed this quiz. You cannot retake it.', 'warning')
            
            # Get quiz details for display
            cur.execute("""
                SELECT q.*, s.title as story_title
                FROM quizzes q
                JOIN stories s ON q.story_id = s.id
                WHERE q.story_id = %s
            """, (story_id,))
            quiz = cur.fetchone()
            
            # Get THIS STUDENT'S previous attempt details only
            cur.execute("""
                SELECT qq.*, sqa.student_answer, sqa.is_correct
                FROM student_quiz_answers sqa
                JOIN quiz_questions qq ON sqa.question_id = qq.id
                WHERE sqa.attempt_id = %s
                ORDER BY qq.id
            """, (previous_attempt['id'],))
            
            answers = cur.fetchall()
            
            cur.close()
            
            return render_template('student/quiz_result.html', 
                                 quiz=quiz, 
                                 score=previous_attempt['score'], 
                                 passed=previous_attempt['score'] >= quiz['passing_score'],
                                 total_points=10,  # You may need to adjust this
                                 earned_points=previous_attempt['score'],
                                 stats=None,
                                 answers=answers,
                                 questions=[],
                                 is_retake=False)
        
        # Get quiz details if not attempted before
        cur.execute("""
            SELECT q.*, s.title as story_title
            FROM quizzes q
            JOIN stories s ON q.story_id = s.id
            WHERE q.story_id = %s
        """, (story_id,))
        quiz = cur.fetchone()
        
        if not quiz:
            flash('Quiz not found for this story', 'danger')
            return redirect(url_for('student_dashboard'))
        
        # Get quiz questions - ONLY THE QUESTIONS, NO STUDENT ANSWERS
        cur.execute("""
            SELECT * FROM quiz_questions
            WHERE quiz_id = %s
            ORDER BY id
        """, (quiz['id'],))
        questions = cur.fetchall()
        
        if request.method == 'POST':
            # Calculate score
            score = 0
            total_points = 0
            answers = []
            
            for question in questions:
                total_points += question['points']
                student_answer = request.form.get(f'question_{question["id"]}', '')
                
                is_correct = False
                if question['question_type'] == 'multiple_choice':
                    is_correct = student_answer == question['correct_answer']
                elif question['question_type'] == 'true_false':
                    is_correct = student_answer.lower() == question['correct_answer'].lower()
                else:  # short_answer
                    is_correct = student_answer.strip().lower() == question['correct_answer'].strip().lower()
                
                if is_correct:
                    score += question['points']
                
                answers.append({
                    'question_id': question['id'],
                    'student_answer': student_answer,
                    'is_correct': is_correct,
                    'correct_answer': question['correct_answer'],
                    'explanation': question['explanation']
                })
            
            percentage_score = (score / total_points) * 100 if total_points > 0 else 0
            
            # Record attempt
            cur.execute("""
                INSERT INTO student_quiz_attempts (student_id, quiz_id, score, time_taken, submitted_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (student['id'], quiz['id'], percentage_score, request.form.get('time_taken', 0)))
            
            attempt_id = cur.lastrowid
            
            # Record answers - ONLY FOR THIS STUDENT
            for answer in answers:
                cur.execute("""
                    INSERT INTO student_quiz_answers (attempt_id, question_id, student_answer, is_correct)
                    VALUES (%s, %s, %s, %s)
                """, (attempt_id, answer['question_id'], answer['student_answer'], answer['is_correct']))
            
            mysql.connection.commit()
            
            # Get statistics - AGGREGATED DATA ONLY (no individual answers)
            cur.execute("""
                SELECT 
                    COUNT(*) as total_attempts,
                    ROUND(AVG(score), 2) as average_score,
                    SUM(CASE WHEN score >= %s THEN 1 ELSE 0 END) as passed_count,
                    SUM(CASE WHEN score < %s THEN 1 ELSE 0 END) as failed_count
                FROM student_quiz_attempts
                WHERE quiz_id = %s
            """, (quiz['passing_score'], quiz['passing_score'], quiz['id']))
            
            stats = cur.fetchone()
            
            cur.close()
            
            return render_template('student/quiz_result.html', 
                                 quiz=quiz, 
                                 score=percentage_score, 
                                 passed=percentage_score >= quiz['passing_score'],
                                 total_points=total_points,
                                 earned_points=score,
                                 stats=stats,
                                 answers=answers,  # This student's answers only
                                 questions=questions,
                                 is_retake=False)
        
        cur.close()
        return render_template('student/quiz.html', quiz=quiz, questions=questions)
    except Exception as e:
        flash(f'Error loading quiz: {str(e)}', 'danger')
        return redirect(url_for('student_dashboard'))
# main code 
@app.route('/student/profile')
@student_required
def student_profile():
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT s.* FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE u.id = %s
        """, (session['user_id'],))
        
        student = cur.fetchone()
        
        # Get quiz performance
        # cur.execute("""
        #     SELECT sqa.score, sqa.submitted_at, s.title as story_title
        #     FROM student_quiz_attempts sqa
        #     JOIN quizzes q ON sqa.quiz_id = q.id
        #     JOIN stories s ON q.story_id = s.id
        #     WHERE sqa.student_id = %s
        #     ORDER BY sqa.submitted_at DESC
        # """, (student['id'],))
        
        # quiz_results = cur.fetchall()
        cur.execute("""
            SELECT sqa.score, sqa.submitted_at, s.title as story_title, q.passing_score
            FROM student_quiz_attempts sqa
            JOIN quizzes q ON sqa.quiz_id = q.id
            JOIN stories s ON q.story_id = s.id
            WHERE sqa.student_id = %s
            ORDER BY sqa.submitted_at DESC
        """, (student['id'],))

        quiz_results = cur.fetchall()

        # Get reading progress
        cur.execute("""
            SELECT COUNT(*) as total_stories_read,
                   SUM(CASE WHEN sp.is_completed THEN 1 ELSE 0 END) as completed_stories
            FROM student_progress sp
            WHERE sp.student_id = %s
        """, (student['id'],))
        
        reading_stats = cur.fetchone()
        
        cur.close()
        
        return render_template('student/profile.html', 
                             student=student, 
                             quiz_results=quiz_results,
                             reading_stats=reading_stats)
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'danger')
        return redirect(url_for('student_dashboard'))
    
# @app.route('/student/profile')
# @student_required
# def student_profile():
#     try:
#         cur = mysql.connection.cursor()

#         # Get student details
#         cur.execute("""
#             SELECT s.* 
#             FROM students s
#             JOIN users u ON s.user_id = u.id
#             WHERE u.id = %s
#         """, (session['user_id'],))
#         student = cur.fetchone()

#         if not student:
#             flash('Student profile not found', 'danger')
#             return redirect(url_for('student_dashboard'))

#         # Get ALL quiz attempts (REMOVED LIMIT)
#         cur.execute("""
#             SELECT 
#                 sqa.score,
#                 sqa.submitted_at,
#                 s.title AS story_title
#             FROM student_quiz_attempts sqa
#             JOIN quizzes q ON sqa.quiz_id = q.id
#             JOIN stories s ON q.story_id = s.id
#             WHERE sqa.student_id = %s
#             ORDER BY sqa.submitted_at DESC
#         """, (student['id'],))
#         quiz_results = cur.fetchall()

#         # Reading progress stats
#         cur.execute("""
#             SELECT 
#                 COUNT(DISTINCT sp.story_id) AS total_stories_read,
#                 SUM(CASE WHEN sp.is_completed = 1 THEN 1 ELSE 0 END) AS completed_stories
#             FROM student_progress sp
#             WHERE sp.student_id = %s
#         """, (student['id'],))
#         reading_stats = cur.fetchone()

#         cur.close()

#         return render_template(
#             'student/profile.html',
#             student=student,
#             quiz_results=quiz_results,
#             reading_stats=reading_stats
#         )

#     except Exception as e:
#         flash(f'Error loading profile: {str(e)}', 'danger')
#         return redirect(url_for('student_dashboard'))

# Add this API endpoint to check quiz attempt status
@app.route('/api/check_quiz_attempt/<int:story_id>')
@student_required
def check_quiz_attempt(story_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get student ID
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        
        # Check if quiz has been attempted
        cur.execute("""
            SELECT COUNT(*) as attempted
            FROM student_quiz_attempts sqa
            JOIN quizzes q ON sqa.quiz_id = q.id
            WHERE q.story_id = %s AND sqa.student_id = %s
        """, (story_id, student['id']))
        
        result = cur.fetchone()
        cur.close()
        
        return jsonify({
            'attempted': result['attempted'] > 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add this route to view previous quiz results
# @app.route('/student/quiz/results/<int:story_id>')
# @student_required
# def view_quiz_results(story_id):
#     try:
#         cur = mysql.connection.cursor()
        
#         # Get student ID
#         cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
#         student = cur.fetchone()
        
#         # Get quiz details
#         cur.execute("""
#             SELECT q.*, s.title as story_title
#             FROM quizzes q
#             JOIN stories s ON q.story_id = s.id
#             WHERE q.story_id = %s
#         """, (story_id,))
#         quiz = cur.fetchone()
        
#         if not quiz:
#             flash('Quiz not found for this story', 'danger')
#             return redirect(url_for('student_dashboard'))
        
#         # Get latest attempt
#         cur.execute("""
#             SELECT sqa.*
#             FROM student_quiz_attempts sqa
#             WHERE sqa.quiz_id = %s AND sqa.student_id = %s
#             ORDER BY sqa.submitted_at DESC
#             LIMIT 1
#         """, (quiz['id'], student['id']))
        
#         attempt = cur.fetchone()
        
#         if not attempt:
#             flash('You have not attempted this quiz yet', 'warning')
#             return redirect(url_for('student_dashboard'))
        
#         # Get answers for this attempt
#         cur.execute("""
#             SELECT qq.*, sqa.student_answer, sqa.is_correct
#             FROM student_quiz_answers sqa
#             JOIN quiz_questions qq ON sqa.question_id = qq.id
#             WHERE sqa.attempt_id = %s
#             ORDER BY qq.id
#         """, (attempt['id'],))
        
#         answers = cur.fetchall()
        
#         cur.close()
        
#         return render_template('student/quiz_previous_result.html',
#                              quiz=quiz,
#                              attempt=attempt,
#                              answers=answers,
#                              passed=attempt['score'] >= quiz['passing_score'])
#     except Exception as e:
#         flash(f'Error loading quiz results: {str(e)}', 'danger')
#         return redirect(url_for('student_dashboard'))
@app.route('/student/quiz/results/<int:story_id>')
@student_required
def view_quiz_results(story_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get student ID
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        
        # Get quiz details
        cur.execute("""
            SELECT q.*, s.title as story_title
            FROM quizzes q
            JOIN stories s ON q.story_id = s.id
            WHERE q.story_id = %s
        """, (story_id,))
        quiz = cur.fetchone()
        
        if not quiz:
            flash('Quiz not found for this story', 'danger')
            return redirect(url_for('student_dashboard'))
        
        # Get THIS STUDENT'S latest attempt only
        cur.execute("""
            SELECT sqa.*
            FROM student_quiz_attempts sqa
            WHERE sqa.quiz_id = %s AND sqa.student_id = %s
            ORDER BY sqa.submitted_at DESC
            LIMIT 1
        """, (quiz['id'], student['id']))
        
        attempt = cur.fetchone()
        
        if not attempt:
            flash('You have not attempted this quiz yet', 'warning')
            return redirect(url_for('student_dashboard'))
        
        # Get THIS STUDENT'S answers for this attempt only
        cur.execute("""
            SELECT qq.*, sqa.student_answer, sqa.is_correct
            FROM student_quiz_answers sqa
            JOIN quiz_questions qq ON sqa.question_id = qq.id
            WHERE sqa.attempt_id = %s
            ORDER BY qq.id
        """, (attempt['id'],))
        
        answers = cur.fetchall()
        
        cur.close()
        
        return render_template('student/quiz_previous_result.html',
                             quiz=quiz,
                             attempt=attempt,
                             answers=answers,
                             passed=attempt['score'] >= quiz['passing_score'])
    except Exception as e:
        flash(f'Error loading quiz results: {str(e)}', 'danger')
        return redirect(url_for('student_dashboard'))


# ================================ Teacher Portal Routes ==========================================

# main code 
# @app.route('/teacher/dashboard')
# @teacher_required
# def teacher_dashboard():
#     try:
#         cur = mysql.connection.cursor()
        
#         # Get teacher details
#         cur.execute("""
#             SELECT t.* FROM teachers t
#             JOIN users u ON t.user_id = u.id
#             WHERE u.id = %s
#         """, (session['user_id'],))
#         teacher = cur.fetchone()
        
#         # Get statistics
#         cur.execute("""
#             SELECT 
#                 COUNT(DISTINCT s.id) as total_stories,
#                 COUNT(DISTINCT ca.class_level) as total_classes,
#                 COUNT(DISTINCT st.id) as total_students,
#                 AVG(sqa.score) as avg_quiz_score
#             FROM teachers t
#             LEFT JOIN stories s ON t.id = s.teacher_id AND s.is_published = TRUE
#             LEFT JOIN class_assignments ca ON s.id = ca.story_id
#             LEFT JOIN students st ON ca.class_level = st.class_level
#             LEFT JOIN quizzes q ON s.id = q.story_id
#             LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
#             WHERE t.id = %s
#         """, (teacher['id'],))
        
#         stats = cur.fetchone()
        
#         # Get recent stories
#         cur.execute("""
#             SELECT s.*, 
#                    COUNT(DISTINCT sp.student_id) as student_count,
#                    COUNT(DISTINCT sqa.id) as quiz_attempts
#             FROM stories s
#             LEFT JOIN student_progress sp ON s.id = sp.story_id
#             LEFT JOIN quizzes q ON s.id = q.story_id
#             LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
#             WHERE s.teacher_id = %s
#             GROUP BY s.id
#             ORDER BY s.created_at DESC
#             LIMIT 5
#         """, (teacher['id'],))
        
#         recent_stories = cur.fetchall()
        
#         # Get recent student activity
#         cur.execute("""
#             SELECT st.first_name, st.last_name, st.class_level, s.title as story_title,
#                    sp.completed_at, sqa.score as quiz_score
#             FROM student_progress sp
#             JOIN students st ON sp.student_id = st.id
#             JOIN stories s ON sp.story_id = s.id
#             LEFT JOIN quizzes q ON s.id = q.story_id
#             LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id AND st.id = sqa.student_id
#             WHERE s.teacher_id = %s AND sp.is_completed = TRUE
#             ORDER BY sp.completed_at DESC
#             LIMIT 10
#         """, (teacher['id'],))
        
#         recent_activity = cur.fetchall()
        
#         cur.close()
        
#         return render_template('teacher/dashboard.html', 
#                              teacher=teacher, 
#                              stats=stats, 
#                              recent_stories=recent_stories,
#                              recent_activity=recent_activity)
#     except Exception as e:
#         flash(f'Error loading dashboard: {str(e)}', 'danger')
#         return redirect(url_for('logout'))
@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    try:
        cur = mysql.connection.cursor()
        
        # Get teacher details
        cur.execute("""
            SELECT t.* FROM teachers t
            JOIN users u ON t.user_id = u.id
            WHERE u.id = %s
        """, (session['user_id'],))
        teacher = cur.fetchone()
        
        # Get statistics
        cur.execute("""
            SELECT 
                COUNT(DISTINCT s.id) as total_stories,
                COUNT(DISTINCT ca.class_level) as total_classes,
                COUNT(DISTINCT st.id) as total_students,
                AVG(sqa.score) as avg_quiz_score
            FROM teachers t
            LEFT JOIN stories s ON t.id = s.teacher_id AND s.is_published = TRUE
            LEFT JOIN class_assignments ca ON s.id = ca.story_id
            LEFT JOIN students st ON ca.class_level = st.class_level
            LEFT JOIN quizzes q ON s.id = q.story_id
            LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
            WHERE t.id = %s
        """, (teacher['id'],))
        
        stats = cur.fetchone()
        
        # Get recent stories
        cur.execute("""
            SELECT s.*, 
                   COUNT(DISTINCT sp.student_id) as student_count,
                   COUNT(DISTINCT sqa.id) as quiz_attempts
            FROM stories s
            LEFT JOIN student_progress sp ON s.id = sp.story_id
            LEFT JOIN quizzes q ON s.id = q.story_id
            LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
            WHERE s.teacher_id = %s
            GROUP BY s.id
            ORDER BY s.created_at DESC
            LIMIT 5
        """, (teacher['id'],))
        
        recent_stories = cur.fetchall()
        
        # Get recent student activity
        cur.execute("""
            SELECT st.first_name, st.last_name, st.class_level, s.title as story_title,
                   sp.completed_at, sqa.score as quiz_score
            FROM student_progress sp
            JOIN students st ON sp.student_id = st.id
            JOIN stories s ON sp.story_id = s.id
            LEFT JOIN quizzes q ON s.id = q.story_id
            LEFT JOIN student_quiz_attempts sqa 
                   ON q.id = sqa.quiz_id AND st.id = sqa.student_id
            WHERE s.teacher_id = %s AND sp.is_completed = TRUE
            ORDER BY sp.completed_at DESC
            LIMIT 10
        """, (teacher['id'],))
        
        recent_activity = cur.fetchall()

        # ================== CHAT STUDENTS (ADDED) ==================
        cur.execute("""
            SELECT cc.id, s.first_name, s.last_name
            FROM chat_conversations cc
            JOIN students s ON s.id = cc.student_id
            WHERE cc.teacher_id = %s
        """, (teacher['id'],))
        
        chat_students = cur.fetchall()

        # Get unread count for teacher
        cur.execute("""
            SELECT COUNT(*) as unread_count
            FROM chat_messages cm
            JOIN chat_conversations cc ON cm.conversation_id = cc.id
            WHERE cc.teacher_id = %s 
              AND cm.sender_type = 'student'
              AND cm.is_read = FALSE
        """, (teacher['id'],))
        
        unread_result = cur.fetchone()
        unread_count = unread_result['unread_count'] if unread_result else 0

        # ============================================================

        cur.close()
        
        return render_template(
            'teacher/dashboard.html', 
            teacher=teacher, 
            stats=stats, 
            recent_stories=recent_stories,
            recent_activity=recent_activity,
            chat_students=chat_students,
            unread_count=unread_count
        )
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('logout'))

    
@app.route('/teacher/stories')
@teacher_required
def teacher_stories():
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
        teacher = cur.fetchone()
        
        cur.execute("""
            SELECT s.*, 
                   COUNT(DISTINCT sp.student_id) as student_count,
                   COUNT(DISTINCT sqa.id) as quiz_attempts,
                   (SELECT COUNT(*) FROM story_pages WHERE story_id = s.id) as page_count
            FROM stories s
            LEFT JOIN student_progress sp ON s.id = sp.story_id
            LEFT JOIN quizzes q ON s.id = q.story_id
            LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
            WHERE s.teacher_id = %s
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """, (teacher['id'],))
        
        stories = cur.fetchall()
        cur.close()
        
        return render_template('teacher/manage_stories.html', stories=stories)
    except Exception as e:
        flash(f'Error loading stories: {str(e)}', 'danger')
        return redirect(url_for('teacher_dashboard'))

# @app.route('/teacher/story/<int:story_id>')
# @teacher_required
# def view_story_details(story_id):
#     try:
#         cur = mysql.connection.cursor()
        
#         # Get story details
#         cur.execute("""
#             SELECT s.*, t.first_name, t.last_name
#             FROM stories s
#             JOIN teachers t ON s.teacher_id = t.id
#             WHERE s.id = %s
#         """, (story_id,))
        
#         story = cur.fetchone()
        
#         if not story:
#             flash('Story not found', 'danger')
#             return redirect(url_for('teacher_stories'))
        
#         # Get story pages
#         cur.execute("""
#             SELECT * FROM story_pages
#             WHERE story_id = %s
#             ORDER BY page_number
#         """, (story_id,))
        
#         pages = cur.fetchall()
        
#         # Get assigned classes
#         cur.execute("""
#             SELECT class_level FROM class_assignments
#             WHERE story_id = %s
#         """, (story_id,))
        
#         assigned_classes = [row['class_level'] for row in cur.fetchall()]
        
#         # Get student progress
#         cur.execute("""
#             SELECT st.first_name, st.last_name, st.class_level, st.roll_number,
#                    sp.current_page, sp.is_completed, sp.completed_at,
#                    (SELECT COUNT(*) FROM story_pages WHERE story_id = %s) as total_pages
#             FROM student_progress sp
#             JOIN students st ON sp.student_id = st.id
#             WHERE sp.story_id = %s
#             ORDER BY st.class_level, st.roll_number
#         """, (story_id, story_id))
        
#         student_progress = cur.fetchall()
        
#         # Check if quiz exists
#         cur.execute("SELECT * FROM quizzes WHERE story_id = %s", (story_id,))
#         quiz = cur.fetchone()
        
#         cur.close()
        
#         return render_template('teacher/story_detail.html',
#                              story=story,
#                              pages=pages,
#                              assigned_classes=assigned_classes,
#                              student_progress=student_progress,
#                              quiz=quiz)
#     except Exception as e:
#         flash(f'Error loading story details: {str(e)}', 'danger')
#         return redirect(url_for('teacher_stories'))



# Update the view_story_details function - fix the query for student progress

# @app.route('/teacher/story/<int:story_id>')
# @teacher_required
# def view_story_details(story_id):
#     try:
#         cur = mysql.connection.cursor()
        
#         # Get story details
#         cur.execute("""
#             SELECT s.*, t.first_name, t.last_name
#             FROM stories s
#             JOIN teachers t ON s.teacher_id = t.id
#             WHERE s.id = %s
#         """, (story_id,))
        
#         story = cur.fetchone()
        
#         if not story:
#             flash('Story not found', 'danger')
#             return redirect(url_for('teacher_stories'))
        
#         # Get story pages
#         cur.execute("""
#             SELECT * FROM story_pages
#             WHERE story_id = %s
#             ORDER BY page_number
#         """, (story_id,))
        
#         pages = cur.fetchall()
        
#         # Get assigned classes
#         cur.execute("""
#             SELECT class_level FROM class_assignments
#             WHERE story_id = %s
#         """, (story_id,))
        
#         assigned_classes = [row['class_level'] for row in cur.fetchall()]
        
#         # FIXED: Updated query to include started_at field
#         cur.execute("""
#             SELECT st.first_name, st.last_name, st.class_level, st.roll_number,
#                    sp.current_page, sp.is_completed, sp.completed_at, sp.started_at,
#                    (SELECT COUNT(*) FROM story_pages WHERE story_id = %s) as total_pages
#             FROM student_progress sp
#             JOIN students st ON sp.student_id = st.id
#             WHERE sp.story_id = %s
#             ORDER BY st.class_level, st.roll_number
#         """, (story_id, story_id))
        
#         student_progress = cur.fetchall()
        
#         # Get quiz info
#         cur.execute("""
#             SELECT q.*, 
#                    COUNT(sqa.id) as attempt_count,
#                    ROUND(AVG(sqa.score), 2) as average_score
#             FROM quizzes q
#             LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
#             WHERE q.story_id = %s
#             GROUP BY q.id
#         """, (story_id,))
        
#         quiz = cur.fetchone()
        
#         # Get available classes for editing
#         cur.execute("SELECT DISTINCT class_level FROM students ORDER BY class_level")
#         classes = [row['class_level'] for row in cur.fetchall()]
        
#         cur.close()
        
#         return render_template('teacher/story_detail.html',
#                              story=story,
#                              pages=pages,
#                              assigned_classes=assigned_classes,
#                              student_progress=student_progress,
#                              quiz=quiz,
#                              classes=classes)
#     except Exception as e:
#         flash(f'Error loading story details: {str(e)}', 'danger')
#         return redirect(url_for('teacher_stories'))

# Update the teacher story details route to include puzzle data
@app.route('/teacher/story/<int:story_id>')
@teacher_required
def view_story_details(story_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get story details
        cur.execute("""
            SELECT s.*, t.first_name, t.last_name
            FROM stories s
            JOIN teachers t ON s.teacher_id = t.id
            WHERE s.id = %s
        """, (story_id,))
        
        story = cur.fetchone()
        
        if not story:
            flash('Story not found', 'danger')
            return redirect(url_for('teacher_stories'))
        
        # Get story pages
        cur.execute("""
            SELECT * FROM story_pages
            WHERE story_id = %s
            ORDER BY page_number
        """, (story_id,))
        
        pages = cur.fetchall()
        
        # Get puzzles for each page
        puzzles_by_page = {}
        for page in pages:
            cur.execute("""
                SELECT spp.*, pt.name as puzzle_type_name
                FROM story_page_puzzles spp
                JOIN puzzle_types pt ON spp.puzzle_type_id = pt.id
                WHERE spp.story_page_id = %s
            """, (page['id'],))
            
            puzzle = cur.fetchone()
            if puzzle:
                puzzles_by_page[page['id']] = puzzle
        
        # Get assigned classes
        cur.execute("""
            SELECT class_level FROM class_assignments
            WHERE story_id = %s
        """, (story_id,))
        
        assigned_classes = [row['class_level'] for row in cur.fetchall()]
        
        # Get student progress
        cur.execute("""
            SELECT st.first_name, st.last_name, st.class_level, st.roll_number,
                   sp.current_page, sp.is_completed, sp.completed_at, sp.started_at,
                   (SELECT COUNT(*) FROM story_pages WHERE story_id = %s) as total_pages
            FROM student_progress sp
            JOIN students st ON sp.student_id = st.id
            WHERE sp.story_id = %s
            ORDER BY st.class_level, st.roll_number
        """, (story_id, story_id))
        
        student_progress = cur.fetchall()
        
        # Get quiz info
        cur.execute("""
            SELECT q.*, 
                   COUNT(sqa.id) as attempt_count,
                   ROUND(AVG(sqa.score), 2) as average_score
            FROM quizzes q
            LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
            WHERE q.story_id = %s
            GROUP BY q.id
        """, (story_id,))
        
        quiz = cur.fetchone()
        
        # Get available classes for editing
        cur.execute("SELECT DISTINCT class_level FROM students ORDER BY class_level")
        classes = [row['class_level'] for row in cur.fetchall()]
        
        cur.close()
        
        return render_template('teacher/story_detail.html',
                             story=story,
                             pages=pages,
                             puzzles_by_page=puzzles_by_page,
                             assigned_classes=assigned_classes,
                             student_progress=student_progress,
                             quiz=quiz,
                             classes=classes)
    except Exception as e:
        flash(f'Error loading story details: {str(e)}', 'danger')
        return redirect(url_for('teacher_stories'))
    

# # main   
# @app.route('/teacher/story/create', methods=['GET', 'POST'])
# @teacher_required
# def create_story():
#     if request.method == 'POST':
#         try:
#             cur = mysql.connection.cursor()
#             cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
#             teacher = cur.fetchone()
            
#             title = request.form.get('title')
#             description = request.form.get('description')
#             is_published = request.form.get('is_published') == 'on'
#             assigned_classes = request.form.getlist('assigned_classes')
            
#             # Save cover image
#             cover_image = None
#             if 'cover_image' in request.files:
#                 file = request.files['cover_image']
#                 if file and file.filename != '' and allowed_file(file.filename):
#                     filename = secure_filename(f"{int(time.time())}_{file.filename}")
#                     filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'stories', filename)
#                     os.makedirs(os.path.dirname(filepath), exist_ok=True)
#                     file.save(filepath)
#                     cover_image = filename
            
#             # Create story
#             cur.execute("""
#                 INSERT INTO stories (teacher_id, title, description, cover_image, is_published)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, (teacher['id'], title, description, cover_image, is_published))
            
#             story_id = cur.lastrowid
            
#             # Save story pages
#             pages_data = request.form.get('pages_data')
#             if pages_data:
#                 pages = json.loads(pages_data)
                
#                 # Handle page images from form data
#                 for i, page in enumerate(pages, 1):
#                     page_number = i
                    
#                     # Get the uploaded file for this page
#                     page_file_key = f'page_image_{page_number}'
                    
#                     image_url = 'default_page_image.jpg'  # Default image
                    
#                     # Check if file was uploaded for this page
#                     if page_file_key in request.files:
#                         file = request.files[page_file_key]
#                         if file and file.filename != '' and allowed_file(file.filename):
#                             # Save the page image
#                             filename = secure_filename(f"{story_id}_page_{page_number}_{int(time.time())}_{file.filename}")
#                             filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'story_pages', filename)
#                             os.makedirs(os.path.dirname(filepath), exist_ok=True)
#                             file.save(filepath)
#                             image_url = filename
                    
#                     # Insert page data
#                     cur.execute("""
#                         INSERT INTO story_pages (story_id, page_number, image_url, text_content, important_notes, duration_seconds)
#                         VALUES (%s, %s, %s, %s, %s, %s)
#                     """, (story_id, page_number, image_url, page.get('text', ''), 
#                           page.get('notes', ''), page.get('duration', 10)))
            
#             # Assign to classes
#             for class_level in assigned_classes:
#                 if class_level.strip():
#                     cur.execute("""
#                         INSERT INTO class_assignments (story_id, class_level, assigned_by)
#                         VALUES (%s, %s, %s)
#                     """, (story_id, class_level.strip(), teacher['id']))
            
#             mysql.connection.commit()
#             cur.close()
            
#             flash('Story created successfully!', 'success')
#             return redirect(url_for('teacher_stories'))
            
#         except Exception as e:
#             mysql.connection.rollback()
#             app.logger.error(f"Error creating story: {str(e)}")
#             flash(f'Error creating story: {str(e)}', 'danger')
#             return redirect(url_for('create_story'))
    
#     # Get available classes
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT DISTINCT class_level FROM students ORDER BY class_level")
#     classes = [row['class_level'] for row in cur.fetchall()]
#     cur.close()
    
#     return render_template('teacher/create_story.html', classes=classes)
@app.route('/teacher/story/create', methods=['GET', 'POST'])
@teacher_required
def create_story():
    if request.method == 'POST':
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
            teacher = cur.fetchone()

            title = request.form.get('title')
            description = request.form.get('description')
            is_published = request.form.get('is_published') == 'on'
            assigned_classes = request.form.getlist('assigned_classes')

            # ---------------- SAVE COVER IMAGE ----------------
            cover_image = None
            if 'cover_image' in request.files:
                file = request.files['cover_image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"{int(time.time())}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'stories', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    cover_image = filename

            # ---------------- CREATE STORY ----------------
            cur.execute("""
                INSERT INTO stories (teacher_id, title, description, cover_image, is_published)
                VALUES (%s, %s, %s, %s, %s)
            """, (teacher['id'], title, description, cover_image, is_published))

            story_id = cur.lastrowid

            # ---------------- SAVE STORY PAGES (NO JSON) ----------------
            page_number = 1

            while True:
                text = request.form.get(f'page_text_{page_number}')
                if not text:
                    break

                notes = request.form.get(f'page_notes_{page_number}', '')
                duration = request.form.get(f'page_duration_{page_number}', 10)

                page_file_key = f'page_image_{page_number}'
                image_url = 'default_page_image.jpg'

                if page_file_key in request.files:
                    file = request.files[page_file_key]
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(
                            f"{story_id}_page_{page_number}_{int(time.time())}_{file.filename}"
                        )
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'story_pages', filename)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        file.save(filepath)
                        image_url = filename

                cur.execute("""
                    INSERT INTO story_pages
                    (story_id, page_number, image_url, text_content, important_notes, duration_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    story_id,
                    page_number,
                    image_url,
                    text,
                    notes,
                    int(duration)
                ))

                page_number += 1

            # ---------------- ASSIGN TO CLASSES ----------------
            for class_level in assigned_classes:
                if class_level.strip():
                    cur.execute("""
                        INSERT INTO class_assignments (story_id, class_level, assigned_by)
                        VALUES (%s, %s, %s)
                    """, (story_id, class_level.strip(), teacher['id']))

            mysql.connection.commit()
            cur.close()

            flash('Story created successfully!', 'success')
            return redirect(url_for('teacher_stories'))

        except Exception as e:
            import traceback
            traceback.print_exc()
            mysql.connection.rollback()
            flash(f'Error creating story: {str(e)}', 'danger')
            return redirect(url_for('create_story'))

    # ---------------- GET ----------------
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT class_level FROM students ORDER BY class_level")
    classes = [row['class_level'] for row in cur.fetchall()]
    cur.close()

    return render_template('teacher/create_story.html', classes=classes)
# main
# @app.route('/teacher/story/<int:story_id>/edit', methods=['GET', 'POST'])
# @teacher_required
# def edit_story(story_id):
#     cur = mysql.connection.cursor()
    
#     # Check if teacher owns this story
#     cur.execute("SELECT teacher_id FROM stories WHERE id = %s", (story_id,))
#     story = cur.fetchone()
    
#     cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
#     teacher = cur.fetchone()
    
#     if not story or story['teacher_id'] != teacher['id']:
#         flash('Access denied', 'danger')
#         return redirect(url_for('teacher_stories'))
    
#     if request.method == 'POST':
#         try:
#             title = request.form.get('title')
#             description = request.form.get('description')
#             is_published = request.form.get('is_published') == 'on'
#             assigned_classes = request.form.getlist('assigned_classes')
            
#             # Update story
#             cur.execute("""
#                 UPDATE stories 
#                 SET title = %s, description = %s, is_published = %s, updated_at = NOW()
#                 WHERE id = %s
#             """, (title, description, is_published, story_id))
            
#             # Update assigned classes
#             cur.execute("DELETE FROM class_assignments WHERE story_id = %s", (story_id,))
            
#             for class_level in assigned_classes:
#                 if class_level.strip():
#                     cur.execute("""
#                         INSERT INTO class_assignments (story_id, class_level, assigned_by)
#                         VALUES (%s, %s, %s)
#                     """, (story_id, class_level.strip(), teacher['id']))
            
#             mysql.connection.commit()
#             flash('Story updated successfully!', 'success')
            
#         except Exception as e:
#             mysql.connection.rollback()
#             flash(f'Error updating story: {str(e)}', 'danger')
    
#     return redirect(url_for('view_story_details', story_id=story_id))

@app.route('/teacher/story/<int:story_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_story(story_id):
    cur = mysql.connection.cursor()

    # ---------------- OWNERSHIP CHECK ----------------
    cur.execute("SELECT teacher_id FROM stories WHERE id = %s", (story_id,))
    story = cur.fetchone()

    cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
    teacher = cur.fetchone()

    if not story or story['teacher_id'] != teacher['id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_stories'))

    # ---------------- POST (UPDATE) ----------------
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            is_published = request.form.get('is_published') == 'on'
            assigned_classes = request.form.getlist('assigned_classes')

            # -------- UPDATE COVER IMAGE (OPTIONAL) --------
            cover_image = None
            if 'cover_image' in request.files:
                file = request.files['cover_image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"{int(time.time())}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'stories', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    cover_image = filename

            # -------- UPDATE STORY --------
            if cover_image:
                cur.execute("""
                    UPDATE stories
                    SET title = %s,
                        description = %s,
                        cover_image = %s,
                        is_published = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (title, description, cover_image, is_published, story_id))
            else:
                cur.execute("""
                    UPDATE stories
                    SET title = %s,
                        description = %s,
                        is_published = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (title, description, is_published, story_id))

            # -------- UPDATE ASSIGNED CLASSES --------
            cur.execute("DELETE FROM class_assignments WHERE story_id = %s", (story_id,))
            for class_level in assigned_classes:
                if class_level.strip():
                    cur.execute("""
                        INSERT INTO class_assignments (story_id, class_level, assigned_by)
                        VALUES (%s, %s, %s)
                    """, (story_id, class_level.strip(), teacher['id']))

            # -------- LOAD EXISTING PAGE IMAGES (CRITICAL FIX) --------
            cur.execute("""
                SELECT page_number, image_url
                FROM story_pages
                WHERE story_id = %s
            """, (story_id,))
            existing_images = {
                row['page_number']: row['image_url']
                for row in cur.fetchall()
            }

            # -------- UPDATE STORY PAGES --------
            cur.execute("DELETE FROM story_pages WHERE story_id = %s", (story_id,))

            # Detect page numbers safely
            page_numbers = []
            for key in request.form.keys():
                if key.startswith('page_text_'):
                    try:
                        num = int(key.replace('page_text_', ''))
                        page_numbers.append(num)
                    except:
                        pass

            page_numbers = sorted(page_numbers)

            for page_number in page_numbers:
                text = request.form.get(f'page_text_{page_number}')
                if not text:
                    continue

                notes = request.form.get(f'page_notes_{page_number}', '')
                duration = request.form.get(f'page_duration_{page_number}', 10)

                page_file_key = f'page_image_{page_number}'

                # ✅ DEFAULT = EXISTING IMAGE FROM DB
                image_url = existing_images.get(page_number, 'default_page_image.jpg')

                # If new image uploaded, replace ONLY that page
                if page_file_key in request.files:
                    file = request.files[page_file_key]
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(
                            f"{story_id}_page_{page_number}_{int(time.time())}_{file.filename}"
                        )
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'story_pages', filename)
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        file.save(filepath)
                        image_url = filename

                cur.execute("""
                    INSERT INTO story_pages
                    (story_id, page_number, image_url, text_content, important_notes, duration_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    story_id,
                    page_number,
                    image_url,
                    text,
                    notes,
                    int(duration)
                ))

            mysql.connection.commit()
            flash('Story and pages updated successfully!', 'success')
            return redirect(url_for('view_story_details', story_id=story_id))

        except Exception as e:
            import traceback
            traceback.print_exc()
            mysql.connection.rollback()
            flash(f'Error updating story: {str(e)}', 'danger')
            return redirect(url_for('edit_story', story_id=story_id))

    # ---------------- GET (LOAD STORY + PAGES) ----------------
    cur.execute("SELECT * FROM stories WHERE id = %s", (story_id,))
    story_data = cur.fetchone()

    cur.execute("""
        SELECT * FROM story_pages
        WHERE story_id = %s
        ORDER BY page_number
    """, (story_id,))
    pages = cur.fetchall()

    cur.execute("SELECT DISTINCT class_level FROM students ORDER BY class_level")
    classes = [row['class_level'] for row in cur.fetchall()]

    cur.execute("SELECT class_level FROM class_assignments WHERE story_id = %s", (story_id,))
    assigned = [row['class_level'] for row in cur.fetchall()]

    cur.close()

    return render_template(
        'teacher/edit_story.html',
        story=story_data,
        pages=pages,
        classes=classes,
        assigned_classes=assigned
    )

@app.route('/teacher/story/<int:story_id>/delete', methods=['POST'])
@teacher_required
def delete_story(story_id):
    try:
        cur = mysql.connection.cursor()
        
        # Check if teacher owns this story
        cur.execute("SELECT teacher_id FROM stories WHERE id = %s", (story_id,))
        story = cur.fetchone()
        
        cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
        teacher = cur.fetchone()
        
        if not story or story['teacher_id'] != teacher['id']:
            flash('Access denied', 'danger')
            return redirect(url_for('teacher_stories'))
        
        # Delete story
        cur.execute("DELETE FROM stories WHERE id = %s", (story_id,))
        mysql.connection.commit()
        
        flash('Story deleted successfully!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error deleting story: {str(e)}', 'danger')
    
    return redirect(url_for('teacher_stories'))

# @app.route('/teacher/story/<int:story_id>/quiz/create', methods=['GET', 'POST'])
# @teacher_required
# def create_quiz(story_id):
#     cur = mysql.connection.cursor()
    
#     # Check if teacher owns this story
#     cur.execute("SELECT teacher_id FROM stories WHERE id = %s", (story_id,))
#     story = cur.fetchone()
    
#     cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
#     teacher = cur.fetchone()
    
#     if not story or story['teacher_id'] != teacher['id']:
#         flash('Access denied', 'danger')
#         return redirect(url_for('teacher_stories'))
    
#     if request.method == 'POST':
#         try:
#             title = request.form.get('title')
#             description = request.form.get('description')
#             time_limit = request.form.get('time_limit', 600)
#             passing_score = request.form.get('passing_score', 60)
            
#             # Create or update quiz
#             cur.execute("SELECT id FROM quizzes WHERE story_id = %s", (story_id,))
#             existing_quiz = cur.fetchone()
            
#             if existing_quiz:
#                 cur.execute("""
#                     UPDATE quizzes 
#                     SET title = %s, description = %s, time_limit = %s, passing_score = %s
#                     WHERE story_id = %s
#                 """, (title, description, time_limit, passing_score, story_id))
#                 quiz_id = existing_quiz['id']
#             else:
#                 cur.execute("""
#                     INSERT INTO quizzes (story_id, title, description, time_limit, passing_score)
#                     VALUES (%s, %s, %s, %s, %s)
#                 """, (story_id, title, description, time_limit, passing_score))
#                 quiz_id = cur.lastrowid
            
#             # Save questions
#             questions_data = request.form.get('questions_data')
#             if questions_data:
#                 questions = json.loads(questions_data)
                
#                 # Delete existing questions
#                 cur.execute("DELETE FROM quiz_questions WHERE quiz_id = %s", (quiz_id,))
                
#                 for question in questions:
#                     cur.execute("""
#                         INSERT INTO quiz_questions 
#                         (quiz_id, question_text, question_type, points, correct_answer, 
#                          option_a, option_b, option_c, option_d, explanation)
#                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#                     """, (quiz_id, question['text'], question['type'], question.get('points', 1),
#                           question['correct_answer'], question.get('option_a'), question.get('option_b'),
#                           question.get('option_c'), question.get('option_d'), question.get('explanation')))
            
#             mysql.connection.commit()
#             cur.close()
            
#             flash('Quiz saved successfully!', 'success')
#             return redirect(url_for('view_story_details', story_id=story_id))
            
#         except Exception as e:
#             mysql.connection.rollback()
#             flash(f'Error saving quiz: {str(e)}', 'danger')
#             return redirect(url_for('create_quiz', story_id=story_id))
    
#     # Get existing quiz if any
#     cur.execute("SELECT * FROM quizzes WHERE story_id = %s", (story_id,))
#     quiz = cur.fetchone()
    
#     questions = []
#     if quiz:
#         cur.execute("SELECT * FROM quiz_questions WHERE quiz_id = %s ORDER BY id", (quiz['id'],))
#         questions = cur.fetchall()
    
#     cur.close()
    
#     return render_template('teacher/add_quiz.html', story_id=story_id, quiz=quiz, questions=questions)
@app.route('/teacher/story/<int:story_id>/quiz/create', methods=['GET', 'POST'])
@teacher_required
def create_quiz(story_id):
    cur = mysql.connection.cursor()

    # Ownership check
    cur.execute("SELECT teacher_id FROM stories WHERE id = %s", (story_id,))
    story = cur.fetchone()

    cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
    teacher = cur.fetchone()

    if not story or story['teacher_id'] != teacher['id']:
        flash('Access denied', 'danger')
        return redirect(url_for('teacher_stories'))

    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')

            # ✅ FIX: minutes → seconds
            time_limit_minutes = int(request.form.get('time_limit', 10))
            time_limit_seconds = time_limit_minutes * 60

            passing_score = int(request.form.get('passing_score', 60))

            # Check existing quiz
            cur.execute("SELECT id FROM quizzes WHERE story_id = %s", (story_id,))
            existing_quiz = cur.fetchone()

            if existing_quiz:
                quiz_id = existing_quiz['id']
                cur.execute("""
                    UPDATE quizzes
                    SET title=%s, description=%s, time_limit=%s, passing_score=%s
                    WHERE id=%s
                """, (title, description, time_limit_seconds, passing_score, quiz_id))
            else:
                cur.execute("""
                    INSERT INTO quizzes (story_id, title, description, time_limit, passing_score)
                    VALUES (%s, %s, %s, %s, %s)
                """, (story_id, title, description, time_limit_seconds, passing_score))
                quiz_id = cur.lastrowid

            # Save questions
            questions_data = request.form.get('questions_data')
            if questions_data:
                questions = json.loads(questions_data)

                cur.execute("DELETE FROM quiz_questions WHERE quiz_id = %s", (quiz_id,))

                for q in questions:
                    cur.execute("""
                        INSERT INTO quiz_questions
                        (quiz_id, question_text, question_type, points, correct_answer,
                         option_a, option_b, option_c, option_d, explanation)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        quiz_id,
                        q['text'],
                        q['type'],
                        q['points'],
                        q['correct_answer'],
                        q.get('option_a'),
                        q.get('option_b'),
                        q.get('option_c'),
                        q.get('option_d'),
                        q.get('explanation')
                    ))

            mysql.connection.commit()
            flash('Quiz saved successfully!', 'success')
            return redirect(url_for('view_story_details', story_id=story_id))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error saving quiz: {str(e)}', 'danger')

    # GET request
    cur.execute("SELECT * FROM quizzes WHERE story_id = %s", (story_id,))
    quiz = cur.fetchone()

    questions = []
    if quiz:
        cur.execute("SELECT * FROM quiz_questions WHERE quiz_id = %s ORDER BY id", (quiz['id'],))
        questions = cur.fetchall()

    cur.close()
    return render_template(
        'teacher/add_quiz.html',
        story_id=story_id,
        quiz=quiz,
        questions=questions
    )

#============================ PDF Download the Story And Quiz Questions & Answers =======================================================

@app.route('/teacher/story/<int:story_id>/download', methods=['GET'])
@teacher_required
def download_story_pdf(story_id):
    """Download story and quiz as PDF"""
    try:
        cur = mysql.connection.cursor()
        
        # Check if teacher owns this story
        cur.execute("SELECT teacher_id FROM stories WHERE id = %s", (story_id,))
        story_owner = cur.fetchone()
        
        cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
        teacher = cur.fetchone()
        
        if not story_owner or story_owner['teacher_id'] != teacher['id']:
            flash('Access denied', 'danger')
            return redirect(url_for('teacher_stories'))
        
        # Get story details
        cur.execute("""
            SELECT s.*, t.first_name, t.last_name
            FROM stories s
            JOIN teachers t ON s.teacher_id = t.id
            WHERE s.id = %s
        """, (story_id,))
        
        story = cur.fetchone()
        
        if not story:
            flash('Story not found', 'danger')
            return redirect(url_for('teacher_stories'))
        
        # Get story pages
        cur.execute("""
            SELECT * FROM story_pages
            WHERE story_id = %s
            ORDER BY page_number
        """, (story_id,))
        
        pages = cur.fetchall()
        
        # Get quiz and questions (WITHOUT answers - for student version)
        cur.execute("SELECT * FROM quizzes WHERE story_id = %s", (story_id,))
        quiz = cur.fetchone()
        
        student_questions = []
        if quiz:
            cur.execute("""
                SELECT id, quiz_id, question_text, question_type, points, 
                       option_a, option_b, option_c, option_d
                FROM quiz_questions
                WHERE quiz_id = %s
                ORDER BY id
            """, (quiz['id'],))
            student_questions = cur.fetchall()
        
        # Get questions WITH answers for answer key
        answer_key_questions = []
        if quiz:
            cur.execute("""
                SELECT id, quiz_id, question_text, question_type, points, 
                       option_a, option_b, option_c, option_d,
                       correct_answer, explanation
                FROM quiz_questions
                WHERE quiz_id = %s
                ORDER BY id
            """, (quiz['id'],))
            answer_key_questions = cur.fetchall()
        
        cur.close()
        
        # Generate PDF
        pdf_buffer = generate_story_pdf(story, pages, quiz, student_questions, answer_key_questions)
        
        # Return PDF as download
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        filename = secure_filename(f"{story['title']}_Story_and_Quiz.pdf")
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('view_story_details', story_id=story_id))

@app.route('/teacher/story/<int:story_id>/preview', methods=['GET'])
@teacher_required
def preview_story_pdf(story_id):
    """Preview story PDF without downloading"""
    try:
        cur = mysql.connection.cursor()
        
        # Check if teacher owns this story
        cur.execute("SELECT teacher_id FROM stories WHERE id = %s", (story_id,))
        story_owner = cur.fetchone()
        
        cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
        teacher = cur.fetchone()
        
        if not story_owner or story_owner['teacher_id'] != teacher['id']:
            flash('Access denied', 'danger')
            return redirect(url_for('teacher_stories'))
        
        # Get story details
        cur.execute("""
            SELECT s.*, t.first_name, t.last_name
            FROM stories s
            JOIN teachers t ON s.teacher_id = t.id
            WHERE s.id = %s
        """, (story_id,))
        
        story = cur.fetchone()
        
        if not story:
            flash('Story not found', 'danger')
            return redirect(url_for('teacher_stories'))
        
        # Get story pages
        cur.execute("""
            SELECT * FROM story_pages
            WHERE story_id = %s
            ORDER BY page_number
        """, (story_id,))
        
        pages = cur.fetchall()
        
        # Get quiz and questions (WITHOUT answers - for student version)
        cur.execute("SELECT * FROM quizzes WHERE story_id = %s", (story_id,))
        quiz = cur.fetchone()
        
        student_questions = []
        if quiz:
            cur.execute("""
                SELECT id, quiz_id, question_text, question_type, points, 
                       option_a, option_b, option_c, option_d
                FROM quiz_questions
                WHERE quiz_id = %s
                ORDER BY id
            """, (quiz['id'],))
            student_questions = cur.fetchall()
        
        # Get questions WITH answers for answer key
        answer_key_questions = []
        if quiz:
            cur.execute("""
                SELECT id, quiz_id, question_text, question_type, points, 
                       option_a, option_b, option_c, option_d,
                       correct_answer, explanation
                FROM quiz_questions
                WHERE quiz_id = %s
                ORDER BY id
            """, (quiz['id'],))
            answer_key_questions = cur.fetchall()
        
        cur.close()
        
        # Generate PDF for preview
        pdf_buffer = generate_story_pdf(story, pages, quiz, student_questions, answer_key_questions)
        
        # Return PDF inline for preview
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        filename = secure_filename(f"{story['title']}_Preview.pdf")
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        
        return response
        
    except Exception as e:
        flash(f'Error generating PDF preview: {str(e)}', 'danger')
        return redirect(url_for('view_story_details', story_id=story_id))

def generate_story_pdf(story, pages, quiz, student_questions, answer_key_questions=None):
    """Generate PDF document for story and quiz"""
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
        title=story['title']
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        spaceAfter=40,
        spaceBefore=60,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2C3E50'),
        fontName='Helvetica-Bold',
        leading=32 
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7F8C8D')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        textColor=colors.HexColor('#3498DB'),
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        textColor=colors.HexColor('#2C3E50'),
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6,
        textColor=colors.HexColor('#34495E'),
        alignment=TA_JUSTIFY
    )
    
    story_text_style = ParagraphStyle(
        'StoryText',
        parent=styles['Normal'],
        fontSize=13,
        spaceAfter=12,
        leading=16,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#2C3E50')
    )
    
    note_style = ParagraphStyle(
        'NoteStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leftIndent=20,
        textColor=colors.HexColor('#E74C3C'),
        fontName='Helvetica-Bold'
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=8,
        textColor=colors.HexColor('#2C3E50'),
        fontName='Helvetica-Bold'
    )
    
    option_style = ParagraphStyle(
        'OptionStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=4,
        leftIndent=20,
        textColor=colors.HexColor('#34495E')
    )
    
    answer_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leftIndent=10,
        textColor=colors.HexColor('#27ae60'),
        fontName='Helvetica-Bold'
    )
    
    explanation_style = ParagraphStyle(
        'ExplanationStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=10,
        textColor=colors.HexColor('#7f8c8d'),
        fontStyle='italic'
    )
    
    # Build story content
    story_content = []
    
    # Cover page with title
    story_content.append(Spacer(1, 2*inch))
    story_content.append(Paragraph(story['title'], title_style))
    story_content.append(Spacer(1, 0.5*inch))
    
    
    # Add cover image if exists
    if story['cover_image'] and story['cover_image'] != 'default_story_image.jpg':
        try:
            # Check if file exists in uploads folder
            upload_folder = app.config['UPLOAD_FOLDER']
            cover_image_path = os.path.join(upload_folder, 'stories', story['cover_image'])
            
            if os.path.exists(cover_image_path):
                # Process image from file path
                pil_img = PILImage.open(cover_image_path)
                
                # Calculate dimensions to fit within page
                max_width = 5*inch
                max_height = 4*inch
                
                # Maintain aspect ratio
                width, height = pil_img.size
                aspect_ratio = width / height
                
                if width > max_width:
                    width = max_width
                    height = width / aspect_ratio
                
                if height > max_height:
                    height = max_height
                    width = height * aspect_ratio
                
                # Convert PIL Image to bytes for ReportLab
                img_buffer = io.BytesIO()
                
                # Convert RGBA to RGB if necessary
                if pil_img.mode == 'RGBA':
                    rgb_img = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                    rgb_img.paste(pil_img, mask=pil_img.split()[3])
                    rgb_img.save(img_buffer, format='JPEG', quality=90)
                else:
                    pil_img.save(img_buffer, format='JPEG', quality=90)
                
                img_buffer.seek(0)
                
                # Add image to PDF
                story_content.append(Image(img_buffer, width=width, height=height))
                story_content.append(Spacer(1, 20))
            else:
                print(f"Cover image not found at: {cover_image_path}")
                story_content.append(Paragraph("<i>Cover image not available</i>", normal_style))
        except Exception as e:
            print(f"Error loading cover image: {str(e)}")
            story_content.append(Paragraph("<i>Cover image not available</i>", normal_style))
    
    # Story metadata
    meta_data = [
        f"<b>Author:</b> {story['first_name']} {story['last_name']}",
        f"<b>Created:</b> {story['created_at'].strftime('%B %d, %Y')}",
        f"<b>Status:</b> {'Published' if story['is_published'] else 'Draft'}",
        f"<b>Total Pages:</b> {len(pages)}"
    ]
    
    for meta in meta_data:
        story_content.append(Paragraph(meta, normal_style))
    
    story_content.append(Spacer(1, 30))
    
    # Story description
    if story['description']:
        story_content.append(Paragraph("<b>Story Description:</b>", heading2_style))
        story_content.append(Paragraph(story['description'], story_text_style))
        story_content.append(Spacer(1, 20))
    
    # Page break before story pages
    story_content.append(PageBreak())
    
    # Story pages
    story_content.append(Paragraph("Story Pages", heading_style))
    story_content.append(Spacer(1, 20))
    
    for i, page in enumerate(pages, 1):
        # Page header
        story_content.append(Paragraph(f"<b>Page {page['page_number']}</b>", heading2_style))
        story_content.append(Spacer(1, 10))
        
        # Try to add page image if exists
        if page['image_url'] and page['image_url'] != 'default_page_image.jpg':
            try:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'story_pages', page['image_url'])
                
                if os.path.exists(image_path):
                    # Process image for PDF
                    pil_img = PILImage.open(image_path)
                    
                    # Calculate dimensions to fit within page
                    max_width = 6*inch
                    max_height = 4*inch
                    
                    # Maintain aspect ratio
                    width, height = pil_img.size
                    aspect_ratio = width / height
                    
                    if width > max_width:
                        width = max_width
                        height = width / aspect_ratio
                    
                    if height > max_height:
                        height = max_height
                        width = height * aspect_ratio
                    
                    # Save processed image to buffer
                    img_buffer = io.BytesIO()
                    
                    # Convert RGBA to RGB if necessary
                    if pil_img.mode == 'RGBA':
                        rgb_img = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                        rgb_img.paste(pil_img, mask=pil_img.split()[3])
                        rgb_img.save(img_buffer, format='JPEG', quality=90)
                    else:
                        pil_img.save(img_buffer, format='JPEG', quality=90)
                    
                    img_buffer.seek(0)
                    
                    # Add image to PDF
                    story_content.append(Image(img_buffer, width=width, height=height))
                    story_content.append(Spacer(1, 10))
            except Exception as e:
                print(f"Error loading page image {page['image_url']}: {str(e)}")
                # Don't add placeholder, just continue
        
        # Page text content
        story_content.append(Paragraph("<b>Text Content:</b>", normal_style))
        story_content.append(Paragraph(page['text_content'], story_text_style))
        story_content.append(Spacer(1, 10))
        
        # Important notes (if any)
        if page['important_notes'] and page['important_notes'].strip():
            story_content.append(Paragraph("<b>Important Notes:</b>", normal_style))
            story_content.append(Paragraph(page['important_notes'], note_style))
            story_content.append(Spacer(1, 10))
        
        # Add separator between pages
        if i < len(pages):
            story_content.append(Spacer(1, 20))
            # Add page break every 3 pages for better readability
            if i % 3 == 0:
                story_content.append(PageBreak())
    
    # Add quiz section if quiz exists
    if quiz:
        story_content.append(PageBreak())
        story_content.append(Paragraph("Quiz Assessment", heading_style))
        story_content.append(Spacer(1, 20))
        
        # Quiz info
        quiz_info = [
            f"<b>Quiz Title:</b> {quiz['title']}",
            f"<b>Description:</b> {quiz['description'] or 'No description'}",
            f"<b>Time Limit:</b> {quiz['time_limit'] // 60} minutes",
            f"<b>Passing Score:</b> {quiz['passing_score']}%",
            f"<b>Total Questions:</b> {len(student_questions)}"
        ]
        
        for info in quiz_info:
            story_content.append(Paragraph(info, normal_style))
        
        story_content.append(Spacer(1, 30))
        
        # STUDENT VERSION: Quiz questions (ONLY QUESTIONS - NO ANSWERS)
        if student_questions:
            story_content.append(Paragraph("<b>Questions (Student Version):</b>", heading2_style))
            story_content.append(Paragraph("<i>Answer all questions in the space provided.</i>", normal_style))
            story_content.append(Spacer(1, 15))
            
            for i, question in enumerate(student_questions, 1):
                # Get question type and normalize it
                question_type = question.get('question_type', '').lower().strip()
                
                # Determine display type
                if 'multiple' in question_type or 'choice' in question_type or question_type == 'mcq':
                    type_display = 'Multiple Choice'
                    is_mcq = True
                elif 'true' in question_type or 'false' in question_type:
                    type_display = 'True/False'
                    is_mcq = False
                elif 'short' in question_type or 'answer' in question_type:
                    type_display = 'Short Answer'
                    is_mcq = False
                else:
                    type_display = question.get('question_type', 'Question')
                    is_mcq = False
                
                story_content.append(Paragraph(f"<b>Question {i} ({type_display}) - {question['points']} point(s):</b>", question_style))
                
                # Question text
                story_content.append(Paragraph(question['question_text'], normal_style))
                story_content.append(Spacer(1, 10))
                
                # Options for MCQ (show all options without indicating correct answer)
                if is_mcq:
                    # Check if any options exist
                    has_options = False
                    
                    # Option A
                    if question.get('option_a'):
                        option_a = str(question['option_a']).strip()
                        if option_a:
                            story_content.append(Paragraph(f"A) {option_a}", option_style))
                            has_options = True
                    
                    # Option B
                    if question.get('option_b'):
                        option_b = str(question['option_b']).strip()
                        if option_b:
                            story_content.append(Paragraph(f"B) {option_b}", option_style))
                            has_options = True
                    
                    # Option C
                    if question.get('option_c'):
                        option_c = str(question['option_c']).strip()
                        if option_c:
                            story_content.append(Paragraph(f"C) {option_c}", option_style))
                            has_options = True
                    
                    # Option D
                    if question.get('option_d'):
                        option_d = str(question['option_d']).strip()
                        if option_d:
                            story_content.append(Paragraph(f"D) {option_d}", option_style))
                            has_options = True
                    
                    if has_options:
                        story_content.append(Spacer(1, 10))
                        story_content.append(Paragraph("Answer: __________", option_style))
                    else:
                        story_content.append(Paragraph("(No options provided)", option_style))
                        story_content.append(Paragraph("Answer: __________", option_style))
                
                # For true/false
                elif type_display == 'True/False':
                    story_content.append(Paragraph("Circle one: True / False", option_style))
                
                # For short answer
                elif type_display == 'Short Answer':
                    story_content.append(Paragraph("Answer: ___________________________________", option_style))
                    story_content.append(Paragraph("_________________________________________", option_style))
                
                # Add space between questions
                if i < len(student_questions):
                    story_content.append(Spacer(1, 20))
                else:
                    story_content.append(Spacer(1, 30))
        
        # Add answer key section (for teachers only)
        if answer_key_questions:
            story_content.append(PageBreak())
            story_content.append(Paragraph("Quiz Answer Key (For Teachers Only)", heading_style))
            story_content.append(Spacer(1, 20))
            
            # Answer key instructions
            story_content.append(Paragraph("<b>Note:</b> This section contains the correct answers and explanations.", note_style))
            story_content.append(Spacer(1, 20))
            
            for i, question in enumerate(answer_key_questions, 1):
                # Get question type and normalize it
                question_type = question.get('question_type', '').lower().strip()
                
                # Determine display type
                if 'multiple' in question_type or 'choice' in question_type or question_type == 'mcq':
                    type_display = 'Multiple Choice'
                    is_mcq = True
                elif 'true' in question_type or 'false' in question_type:
                    type_display = 'True/False'
                    is_mcq = False
                elif 'short' in question_type or 'answer' in question_type:
                    type_display = 'Short Answer'
                    is_mcq = False
                else:
                    type_display = question.get('question_type', 'Question')
                    is_mcq = False
                
                story_content.append(Paragraph(f"<b>Question {i} ({type_display}) - {question['points']} point(s):</b>", question_style))
                
                # Question text
                story_content.append(Paragraph(question['question_text'], normal_style))
                story_content.append(Spacer(1, 10))
                
                # Show correct answer
                if 'correct_answer' in question and question['correct_answer']:
                    correct_answer = str(question['correct_answer']).strip()
                    
                    if is_mcq:
                        # Map correct answer to option text
                        if correct_answer.upper() == 'A':
                            answer_text = str(question.get('option_a', 'Option A')).strip()
                            story_content.append(Paragraph(f"<b>Correct Answer:</b> A) {answer_text}", answer_style))
                        elif correct_answer.upper() == 'B':
                            answer_text = str(question.get('option_b', 'Option B')).strip()
                            story_content.append(Paragraph(f"<b>Correct Answer:</b> B) {answer_text}", answer_style))
                        elif correct_answer.upper() == 'C':
                            answer_text = str(question.get('option_c', 'Option C')).strip()
                            story_content.append(Paragraph(f"<b>Correct Answer:</b> C) {answer_text}", answer_style))
                        elif correct_answer.upper() == 'D':
                            answer_text = str(question.get('option_d', 'Option D')).strip()
                            story_content.append(Paragraph(f"<b>Correct Answer:</b> D) {answer_text}", answer_style))
                        else:
                            story_content.append(Paragraph(f"<b>Correct Answer:</b> {correct_answer}", answer_style))
                    else:
                        story_content.append(Paragraph(f"<b>Correct Answer:</b> {correct_answer}", answer_style))
                else:
                    story_content.append(Paragraph("<b>Correct Answer:</b> Not specified", answer_style))
                
                # Show explanation if available
                if 'explanation' in question and question['explanation']:
                    explanation = str(question['explanation']).strip()
                    if explanation:
                        story_content.append(Paragraph(f"<b>Explanation:</b> {explanation}", explanation_style))
                
                # Add space between questions
                if i < len(answer_key_questions):
                    story_content.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story_content)
    
    buffer.seek(0)
    return buffer


#=========================================================================================

@app.route('/teacher/students')
@teacher_required
def view_students():
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT s.*, u.email, u.created_at as account_created,
                   (SELECT COUNT(*) FROM student_progress sp WHERE sp.student_id = s.id AND sp.is_completed = TRUE) as completed_stories,
                   (SELECT COUNT(*) FROM student_quiz_attempts sqa WHERE sqa.student_id = s.id) as quiz_attempts,
                   (SELECT AVG(score) FROM student_quiz_attempts sqa WHERE sqa.student_id = s.id) as avg_score
            FROM students s
            JOIN users u ON s.user_id = u.id
            ORDER BY s.class_level, s.roll_number
        """)
        
        students = cur.fetchall()
        
        # Get class statistics
        cur.execute("""
            SELECT class_level, COUNT(*) as student_count
            FROM students
            GROUP BY class_level
            ORDER BY class_level
        """)
        
        class_stats = cur.fetchall()
        
        cur.close()
        
        return render_template('teacher/view_students.html', students=students, class_stats=class_stats)
    except Exception as e:
        flash(f'Error loading students: {str(e)}', 'danger')
        return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/analytics')
@teacher_required
def analytics():
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("SELECT id FROM teachers WHERE user_id = %s", (session['user_id'],))
        teacher = cur.fetchone()
        
        # Get overall statistics
        cur.execute("""
            SELECT 
                COUNT(DISTINCT s.id) as total_stories,
                COUNT(DISTINCT st.id) as total_students,
                COUNT(DISTINCT sqa.id) as total_quiz_attempts,
                AVG(sqa.score) as overall_avg_score,
                MAX(sqa.score) as highest_score,
                MIN(sqa.score) as lowest_score
            FROM teachers t
            LEFT JOIN stories s ON t.id = s.teacher_id
            LEFT JOIN class_assignments ca ON s.id = ca.story_id
            LEFT JOIN students st ON ca.class_level = st.class_level
            LEFT JOIN quizzes q ON s.id = q.story_id
            LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
            WHERE t.id = %s
        """, (teacher['id'],))
        
        overall_stats = cur.fetchone()
        
        # Get story-wise analytics
        cur.execute("""
            SELECT 
                s.id,
                s.title,
                COUNT(DISTINCT sp.student_id) as students_assigned,
                COUNT(DISTINCT CASE WHEN sp.is_completed THEN sp.student_id END) as students_completed,
                COUNT(DISTINCT sqa.id) as quiz_attempts,
                AVG(sqa.score) as avg_quiz_score,
                COUNT(DISTINCT CASE WHEN sqa.score >= q.passing_score THEN sqa.student_id END) as students_passed
            FROM stories s
            LEFT JOIN student_progress sp ON s.id = sp.story_id
            LEFT JOIN quizzes q ON s.id = q.story_id
            LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id
            WHERE s.teacher_id = %s
            GROUP BY s.id, s.title
            ORDER BY s.created_at DESC
        """, (teacher['id'],))
        
        story_analytics = cur.fetchall()
        
        # Get class-wise performance
        cur.execute("""
            SELECT 
                st.class_level,
                COUNT(DISTINCT st.id) as total_students,
                COUNT(DISTINCT sp.story_id) as total_stories_assigned,
                AVG(CASE WHEN sp.is_completed THEN 1 ELSE 0 END) * 100 as completion_rate,
                AVG(sqa.score) as avg_quiz_score
            FROM students st
            LEFT JOIN class_assignments ca ON st.class_level = ca.class_level
            LEFT JOIN student_progress sp ON st.id = sp.student_id AND ca.story_id = sp.story_id
            LEFT JOIN quizzes q ON ca.story_id = q.story_id
            LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id AND st.id = sqa.student_id
            GROUP BY st.class_level
            ORDER BY st.class_level
        """)
        
        class_analytics = cur.fetchall()
        
        # Get recent quiz performance
        cur.execute("""
            SELECT 
                s.title as story_title,
                st.first_name,
                st.last_name,
                st.class_level,
                sqa.score,
                sqa.submitted_at,
                CASE WHEN sqa.score >= q.passing_score THEN 'Passed' ELSE 'Failed' END as result
            FROM student_quiz_attempts sqa
            JOIN quizzes q ON sqa.quiz_id = q.id
            JOIN stories s ON q.story_id = s.id
            JOIN students st ON sqa.student_id = st.id
            WHERE s.teacher_id = %s
            ORDER BY sqa.submitted_at DESC
        """, (teacher['id'],))
        
        recent_quiz_results = cur.fetchall()
        
        cur.close()
        
        return render_template('teacher/analytics.html', 
                             overall_stats=overall_stats,
                             story_analytics=story_analytics,
                             class_analytics=class_analytics,
                             recent_quiz_results=recent_quiz_results)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'danger')
        return redirect(url_for('teacher_dashboard'))

# # API Routes for real-time updates
# @app.route('/api/student_progress/<int:story_id>')
# @teacher_required
# def get_student_progress(story_id):
#     try:
#         cur = mysql.connection.cursor()
        
#         cur.execute("""
#             SELECT 
#                 st.first_name,
#                 st.last_name,
#                 st.class_level,
#                 st.roll_number,
#                 sp.current_page,
#                 sp.is_completed,
#                 sp.started_at,
#                 sp.completed_at,
#                 sqa.score as quiz_score,
#                 sqa.submitted_at as quiz_submitted_at
#             FROM students st
#             JOIN student_progress sp ON st.id = sp.student_id
#             LEFT JOIN quizzes q ON sp.story_id = q.story_id
#             LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id AND st.id = sqa.student_id
#             WHERE sp.story_id = %s
#             ORDER BY sp.is_completed, sp.current_page DESC
#         """, (story_id,))
        
#         progress = cur.fetchall()
#         cur.close()
        
#         return jsonify(progress)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
@app.route('/api/student_progress/<int:story_id>')
@teacher_required
def get_student_progress(story_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get total pages for this story
        cur.execute("SELECT COUNT(*) as total_pages FROM story_pages WHERE story_id = %s", (story_id,))
        total_pages_result = cur.fetchone()
        total_pages = total_pages_result['total_pages'] if total_pages_result else 0
        
        cur.execute("""
            SELECT 
                st.first_name,
                st.last_name,
                st.class_level,
                st.roll_number,
                sp.current_page,
                sp.is_completed,
                sp.started_at,
                sp.completed_at,
                sqa.score as quiz_score,
                sqa.submitted_at as quiz_submitted_at,
                -- Calculate actual completion based on current_page vs total pages
                CASE 
                    WHEN sp.current_page >= %s AND %s > 0 
                    THEN TRUE 
                    ELSE sp.is_completed 
                END as actually_completed,
                -- Calculate progress percentage
                CASE 
                    WHEN %s > 0 
                    THEN ROUND((sp.current_page * 100.0) / %s, 1)
                    ELSE 0 
                END as progress_percentage
            FROM students st
            JOIN student_progress sp ON st.id = sp.student_id
            LEFT JOIN quizzes q ON sp.story_id = q.story_id
            LEFT JOIN student_quiz_attempts sqa ON q.id = sqa.quiz_id AND st.id = sqa.student_id
            WHERE sp.story_id = %s
            ORDER BY sp.is_completed DESC, sp.current_page DESC, st.class_level, st.roll_number
        """, (total_pages, total_pages, total_pages, total_pages, story_id))
        
        progress = cur.fetchall()
        cur.close()
        
        return jsonify({
            'progress': progress,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/mark_story_completed', methods=['POST'])
@student_required
def mark_story_completed():
    """Explicitly mark a story as completed"""
    try:
        data = request.json
        story_id = data.get('story_id')
        
        cur = mysql.connection.cursor()
        
        # Get student ID
        cur.execute("SELECT id FROM students WHERE user_id = %s", (session['user_id'],))
        student = cur.fetchone()
        
        # Get total pages
        cur.execute("SELECT COUNT(*) as total_pages FROM story_pages WHERE story_id = %s", (story_id,))
        total_pages_result = cur.fetchone()
        total_pages = total_pages_result['total_pages'] if total_pages_result else 0
        
        # Mark as completed
        cur.execute("""
            UPDATE student_progress 
            SET is_completed = TRUE, 
                completed_at = NOW(),
                current_page = %s
            WHERE student_id = %s AND story_id = %s
        """, (total_pages, student['id'], story_id))
        
        # If no rows affected, insert new record
        if cur.rowcount == 0:
            cur.execute("""
                INSERT INTO student_progress 
                (student_id, story_id, current_page, is_completed, started_at, completed_at)
                VALUES (%s, %s, %s, TRUE, NOW(), NOW())
            """, (student['id'], story_id, total_pages))
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Story marked as completed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/quiz_statistics/<int:quiz_id>')
@teacher_required
def get_quiz_statistics(quiz_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get detailed statistics
        cur.execute("""
            SELECT 
                q.question_text,
                q.question_type,
                q.correct_answer,
                COUNT(sqa.id) as total_answers,
                SUM(CASE WHEN sqa.is_correct THEN 1 ELSE 0 END) as correct_answers,
                GROUP_CONCAT(DISTINCT s.student_answer) as sample_answers
            FROM quiz_questions q
            LEFT JOIN student_quiz_answers s ON q.id = s.question_id
            WHERE q.quiz_id = %s
            GROUP BY q.id
        """, (quiz_id,))
        
        question_stats = cur.fetchall()
        
        # Get score distribution
        cur.execute("""
            SELECT 
                FLOOR(score/10)*10 as score_range,
                COUNT(*) as student_count
            FROM student_quiz_attempts
            WHERE quiz_id = %s
            GROUP BY FLOOR(score/10)*10
            ORDER BY score_range
        """, (quiz_id,))
        
        score_distribution = cur.fetchall()
        
        cur.close()
        
        return jsonify({
            'question_stats': question_stats,
            'score_distribution': score_distribution
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
