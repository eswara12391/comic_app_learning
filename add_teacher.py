#!/usr/bin/env python3
"""Script to add or update a teacher account in the database"""

from werkzeug.security import generate_password_hash
from app import app, mysql

# Teacher information
email = 'soumyaranjanmishra814@gmail.com'
password = 'Soumya@12'
first_name = 'Soumya'
last_name = 'Mishra'

try:
    with app.app_context():
        cursor = mysql.connection.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id, user_type FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            user_id = user['id']
            user_type = user['user_type']
            
            if user_type == 'teacher':
                # Already a teacher, just update password
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "UPDATE users SET password_hash = %s WHERE id = %s",
                    (password_hash, user_id)
                )
                print(f"✓ Teacher account already exists with this email.")
                print(f"  Password has been updated.")
            else:
                # Currently a student, need to convert to teacher
                # First update user_type
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "UPDATE users SET password_hash = %s, user_type = 'teacher' WHERE id = %s",
                    (password_hash, user_id)
                )
                
                # Check if teacher record exists
                cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (user_id,))
                if not cursor.fetchone():
                    # Create teacher record
                    cursor.execute("""
                        INSERT INTO teachers 
                        (user_id, first_name, last_name, email, date_of_birth, gender, address, registration_number)
                        VALUES (%s, %s, %s, %s, '2000-01-01', 'male', 'Address', %s)
                    """, (user_id, first_name, last_name, email, f'REG_{user_id}'))
                
                print(f"✓ Account type updated to teacher!")
                print(f"  Email: {email}")
                print(f"  Password: {password}")
        else:
            # New user - create as teacher
            password_hash = generate_password_hash(password)
            
            cursor.execute(
                "INSERT INTO users (email, password_hash, user_type) VALUES (%s, %s, 'teacher')",
                (email, password_hash)
            )
            user_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO teachers 
                (user_id, first_name, last_name, email, date_of_birth, gender, address, registration_number)
                VALUES (%s, %s, %s, %s, '2000-01-01', 'male', 'Address', %s)
            """, (user_id, first_name, last_name, email, f'REG_{user_id}'))
            
            print(f"✓ New teacher account created!")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
        
        mysql.connection.commit()
        print(f"  Name: {first_name} {last_name}")
        cursor.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)
