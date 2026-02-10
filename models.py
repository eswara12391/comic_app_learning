# # models.py
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime

# # Initialize db here
# db = SQLAlchemy()

# # Now define your StudentDrawing model
# class StudentDrawing(db.Model):
#     """Model to store student's private drawings"""
#     __tablename__ = 'student_drawings'
    
#     id = db.Column(db.Integer, primary_key=True)
#     story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete='CASCADE'), nullable=False)
#     student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
#     drawing_data = db.Column(db.Text, nullable=False)  # Base64 encoded image data
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
#     # Relationships
#     story = db.relationship('Story', backref='student_drawings')
#     student = db.relationship('Student', backref='drawings')
    
#     # Unique constraint: one drawing per student per story
#     __table_args__ = (
#         db.UniqueConstraint('story_id', 'student_id', name='unique_student_drawing'),
#     )
    
#     def __repr__(self):
#         return f'<StudentDrawing {self.id} - Student {self.student_id} - Story {self.story_id}>'