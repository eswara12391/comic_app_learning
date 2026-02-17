#!/usr/bin/env python3
"""
Test script for all API endpoints to verify they work correctly in production.
This script simulates production environment and tests error handling.
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:5000"
STUDENT_USER = "student@test.com"
STUDENT_PASSWORD = "password123"
TEACHER_USER = "teacher@test.com"
TEACHER_PASSWORD = "password123"

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def log_test(self, name, status, details=""):
        """Log test result"""
        result = {
            'test': name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.results.append(result)
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {name}: {status} {details}")
        
    def login_student(self):
        """Login as student"""
        print("\n" + "="*60)
        print("AUTHENTICATING AS STUDENT")
        print("="*60)
        
        data = {
            'email': STUDENT_USER,
            'password': STUDENT_PASSWORD
        }
        
        response = self.session.post(f"{self.base_url}/login", data=data, allow_redirects=False)
        
        if response.status_code == 302 or 'user_id' in self.session.cookies:
            self.log_test("Student Login", "PASS", f"Status: {response.status_code}")
            return True
        else:
            self.log_test("Student Login", "FAIL", f"Status: {response.status_code}")
            return False
    
    def login_teacher(self):
        """Login as teacher"""
        print("\n" + "="*60)
        print("AUTHENTICATING AS TEACHER")
        print("="*60)
        
        data = {
            'email': TEACHER_USER,
            'password': TEACHER_PASSWORD
        }
        
        response = self.session.post(f"{self.base_url}/login", data=data, allow_redirects=False)
        
        if response.status_code == 302 or 'user_id' in self.session.cookies:
            self.log_test("Teacher Login", "PASS", f"Status: {response.status_code}")
            return True
        else:
            self.log_test("Teacher Login", "FAIL", f"Status: {response.status_code}")
            return False
    
    def test_drawing_endpoints(self):
        """Test student drawing API endpoints"""
        print("\n" + "="*60)
        print("TESTING DRAWING ENDPOINTS")
        print("="*60)
        
        # Test save_student_drawing
        payload = {
            'story_id': 1,
            'drawing_data': 'data:image/png;base64,iVBORw0KGgo...'
        }
        
        response = self.session.post(
            f"{self.base_url}/api/save_student_drawing",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log_test("Save Student Drawing", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("Save Student Drawing", "FAIL", f"Error: {data.get('error')}")
        else:
            self.log_test("Save Student Drawing", "FAIL", f"Status: {response.status_code}")
    
    def test_chat_endpoints(self):
        """Test chat API endpoints"""
        print("\n" + "="*60)
        print("TESTING CHAT ENDPOINTS")
        print("="*60)
        
        # Test get_unread_count
        response = self.session.get(f"{self.base_url}/api/chat/unread-count")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data.get('count'), int):
                self.log_test("Get Unread Chat Count", "PASS", f"Count: {data['count']}")
            else:
                self.log_test("Get Unread Chat Count", "FAIL", f"Invalid count format")
        else:
            self.log_test("Get Unread Chat Count", "FAIL", f"Status: {response.status_code}")
    
    def test_classmates_endpoint(self):
        """Test get_student_classmates endpoint"""
        print("\n" + "="*60)
        print("TESTING CLASSMATES ENDPOINT")
        print("="*60)
        
        response = self.session.get(f"{self.base_url}/api/student/classmates")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_test("Get Classmates", "PASS", f"Classmates: {len(data)}")
            else:
                self.log_test("Get Classmates", "FAIL", f"Expected list, got {type(data)}")
        else:
            self.log_test("Get Classmates", "FAIL", f"Status: {response.status_code}")
    
    def test_error_handling(self):
        """Test error handling with invalid parameters"""
        print("\n" + "="*60)
        print("TESTING ERROR HANDLING")
        print("="*60)
        
        # Test missing required parameter
        response = self.session.post(
            f"{self.base_url}/api/save_student_drawing",
            json={}
        )
        
        if response.status_code >= 400:
            self.log_test("Missing Parameter Error Handling", "PASS", f"Status: {response.status_code}")
        else:
            self.log_test("Missing Parameter Error Handling", "FAIL", f"Expected 4xx, got {response.status_code}")
        
        # Test non-existent endpoint
        response = self.session.get(f"{self.base_url}/api/non/existent/endpoint")
        
        if response.status_code == 404:
            self.log_test("Non-existent Endpoint Error Handling", "PASS", f"Status: {response.status_code}")
        else:
            self.log_test("Non-existent Endpoint Error Handling", "FAIL", f"Expected 404, got {response.status_code}")
    
    def test_production_simulation(self):
        """Test production-like scenarios"""
        print("\n" + "="*60)
        print("TESTING PRODUCTION SIMULATION")
        print("="*60)
        
        # Test multiple concurrent-like requests
        print("\nTesting request handling under load...")
        
        for i in range(5):
            response = self.session.get(f"{self.base_url}/api/chat/unread-count")
            if response.status_code == 200:
                print(f"  Request {i+1}: OK")
            else:
                print(f"  Request {i+1}: FAILED (Status: {response.status_code})")
                self.log_test(f"Production Load Test - Request {i+1}", "FAIL", f"Status: {response.status_code}")
                return
        
        self.log_test("Production Load Test", "PASS", "All 5 requests handled correctly")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == "PASS")
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if result['status'] == "FAIL":
                    print(f"  - {result['test']}: {result['details']}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("COMIC LEARNING APP - API ENDPOINT TEST SUITE")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    
    tester = APITester(BASE_URL)
    
    try:
        # Test student endpoints
        if tester.login_student():
            tester.test_drawing_endpoints()
            tester.test_chat_endpoints()
            tester.test_classmates_endpoint()
            tester.test_error_handling()
        
        # Test teacher endpoints
        tester.session.clear()
        if tester.login_teacher():
            tester.test_chat_endpoints()
        
        # Test production simulation
        tester.test_production_simulation()
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        tester.print_summary()
        
        # Save results to file
        with open('test_results.json', 'w') as f:
            json.dump(tester.results, f, indent=2)
        print(f"\nResults saved to test_results.json")

if __name__ == '__main__':
    main()
