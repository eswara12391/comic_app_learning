# Production Debugging Quick Guide

## How to Find Errors in Production

### 1. Start Application with Logging

```bash
# Development (verbose logging)
FLASK_ENV=development FLASK_DEBUG=True python app.py

# Production (info-level logging)
FLASK_ENV=production FLASK_DEBUG=False python app.py
```

### 2. View Real-Time Logs

```bash
# View last 50 lines
tail -50 app.log

# Follow logs (watch as they appear)
tail -f app.log

# Search for errors
grep ERROR app.log

# Search for specific module
grep "submit_puzzle_answer" app.log
tail -100 app.log | grep ERROR
```

### 3. Understanding Log Format

```
2024-01-15 14:30:45,123 - app - INFO - Puzzle answer submission from student user_id: 123
2024-01-15 14:30:45,456 - app - INFO - Processing puzzle 45
2024-01-15 14:30:45,789 - app - WARNING - Missing story_id parameter
2024-01-15 14:30:46,012 - app - ERROR - Error submitting puzzle: Puzzle not found
2024-01-15 14:30:46,345 - app - ERROR - Traceback:
  Traceback (most recent call last):
    File "app.py", line 1847, in submit_puzzle_answer
      puzzle = cur.fetchone()
  MySQLdb.DatabaseError: (1054, "Unknown column 'status' in 'on clause'")
```

### 4. Common Error Messages and Solutions

#### Error: "Student not found for user_id"
```
Check: Is user actually logged in?
Solution: Verify session is maintained, user exists in database
```

#### Error: "Puzzle not found"
```
Check: puzzle_id passed to endpoint
Solution: Verify puzzle exists, check puzzle_id value in logs
```

#### Error: "MySQL connection timeout"
```
Check: Is MySQL server running?
Solution: 
  - Check MySQL: mysql -u root -p
  - Restart MySQL service
  - Restart application
```

#### Error: "Too many connections"
```
Check: Connection pool exhausted
Solution:
  - This should be rare with new error handling
  - Restart application to reset pool
  - Check for connection leaks in logs
```

### 5. Manual Endpoint Testing

```bash
# Test in another terminal
curl -X POST http://localhost:5000/api/chat/unread-count \
  -H "Content-Type: application/json"

# Response if logged in:
{"count": 5, "success": true}

# Response if not logged in:
{"error": "Unauthorized", "code": 401}
```

### 6. File Locations

```
app.py                              # Main application
config.py                           # Configuration
.env                               # Environment variables (CREATE THIS)
test_api_endpoints.py              # Test suite
PRODUCTION_API_UPDATES.md          # Full documentation
PRODUCTION_FIX_SUMMARY.md          # Quick summary
static/                            # Static files (CSS, JS, uploads)
templates/                         # HTML templates
database/                          # Database schema
```

### 7. Enable DEBUG Logging on Production (Temporary)

Edit app.py temporarily:

```python
# Change from:
logging.basicConfig(level=logging.INFO, ...)

# To:
logging.basicConfig(level=logging.DEBUG, ...)
```

This will log:
- All function parameters
- All variable values  
- All database queries
- Much more verbose output

**WARNING**: Remove DEBUG logging when done (performance impact)

### 8. Track Specific User Session

Add to logs:
```bash
grep "user_id: 123" app.log
```

Or search by email:
```bash
grep "student@test.com" app.log
```

### 9. Analyze Error Patterns

```bash
# Count errors by type
grep ERROR app.log | wc -l

# Most common errors
grep ERROR app.log | sort | uniq -c | sort -rn

# Errors in last hour
logs=$(date --date='1 hour ago' +%Y-%m-%d\ %H:%M:%S)
grep "since $logs" app.log | grep ERROR
```

### 10. Create a Deployment Verification Checklist

```
BEFORE DEPLOYMENT:
- [ ] app.py updated
- [ ] .env configured
- [ ] MySQL credentials verified
- [ ] Upload directories exist with correct permissions
- [ ] test_api_endpoints.py runs successfully

AFTER DEPLOYMENT:
- [ ] Application starts without errors
- [ ] Can login as student
- [ ] Can login as teacher  
- [ ] Can perform drawing operation
- [ ] Can send/receive message
- [ ] Unread counts work
- [ ] Can submit puzzle
- [ ] No "An error occurred" messages in UI
- [ ] Specific errors appear in logs
- [ ] All operations complete in < 2 seconds
```

### 11. Emergency Recovery

If production breaks:

```bash
# 1. Stop application
pkill -f "python app.py"

# 2. Check logs for error
tail -100 app.log | grep ERROR

# 3. Fix issue:
   - Update .env if credentials wrong
   - Restart MySQL if connection failed
   - Fix upload directory permissions
   - etc.

# 4. Start application again
python app.py &
tail -f app.log

# 5. Test endpoints work
python test_api_endpoints.py
```

### 12. Performance Monitoring

```bash
# Check response times (if logging timestamps)
grep "Completed\|ERROR" app.log | grep "puzzle"

# Look for patterns:
# - Are pulses consistently taking > 1 second?
# - Are some errors repeating?
# - Is a specific endpoint slow?
```

### 13. User Support Triage

When user reports "An error occurred":

**Ask them**:
1. What were you doing? (submitting puzzle, sending message, etc.)
2. What browser are you using?
3. If button doesn't work, check JavaScript errors (F12)

**Check logs**:
```bash
# Get last 200 lines of errors
grep ERROR app.log | tail -20

# Look for the specific operation
grep "submit_puzzle\|send.*message\|chat" app.log | tail -30
```

**Common causes**:
- MySQL not running
- Upload directory missing/permission denied
- Invalid user_id (table mismatch)
- Session timeout
- Browser cache issue

---

## Quick Checklist When Something Breaks

```
☐ Check if MySQL is running
☐ Check .env file for credentials
☐ Look at last 20 lines of error log
☐ Read the traceback carefully
☐ Check if it's a permission/file issue
☐ Try test_api_endpoints.py to isolate
☐ Restart MySQL vs restart app?
☐ Check upload folder permissions
☐ Check free disk space
☐ Look for "too many connections"
```

---

**Remember**: With the new error handling, all issues will be visible in logs with full traceback. No more generic "An error occurred" messages.
