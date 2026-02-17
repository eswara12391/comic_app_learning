#!/usr/bin/env python3
"""Test script to debug registration and login routes"""

import sys
import logging
from app import app, mysql

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a test client
client = app.test_client()

print("Testing /register/student route...")
try:
    # Test GET request
    response = client.get('/register/student')
    print(f"GET /register/student: {response.status_code}")
    
    # Test POST request with test data
    data = {
        'email': 'test_student@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'first_name': 'Test',
        'middle_name': 'Mid',
        'last_name': 'Student',
        'date_of_birth': '2010-01-01',
        'phone': '1234567890',
        'address': '123 Test St',
        'gender': 'male',
        'class_level': '5',
        'roll_number': 'STU001',
        'parent_full_name': 'Parent',
        'parent_email': 'parent@example.com',
        'parent_phone': '0987654321',
        'parent_relationship': 'Parent'
    }
    response = client.post('/register/student', data=data)
    print(f"POST /register/student: {response.status_code}")
    print(f"Response data: {response.get_data(as_text=True)[:200]}")
    
except Exception as e:
    logger.error(f"Error testing /register/student: {str(e)}", exc_info=True)
    print(f"Error: {str(e)}")

print("\nTesting /login route...")
try:
    # Test GET request
    response = client.get('/login')
    print(f"GET /login: {response.status_code}")
    
    # Test POST request  
    data = {
        'email': 'test@example.com',
        'password': 'testpass'
    }
    response = client.post('/login', data=data)
    print(f"POST /login: {response.status_code}")
    
except Exception as e:
    logger.error(f"Error testing /login: {str(e)}", exc_info=True)
    print(f"Error: {str(e)}")

print("\nDone!")
