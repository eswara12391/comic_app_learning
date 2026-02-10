-- Create database
CREATE DATABASE IF NOT EXISTS comic_learning_db;
USE comic_learning_db;

-- Users table (common for both teachers and students)
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type ENUM('teacher', 'student') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_user_type (user_type),
    INDEX idx_email (email)
);

-- Students table
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    gender ENUM('male', 'female', 'other') NOT NULL,
    class_level VARCHAR(50) NOT NULL,
    roll_number VARCHAR(50) UNIQUE NOT NULL,
    profile_photo VARCHAR(255),
    parent_full_name VARCHAR(255),
    parent_email VARCHAR(255),
    parent_phone VARCHAR(20),
    parent_relationship VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_roll_number (roll_number),
    INDEX idx_class_level (class_level)
);

-- Teachers table
CREATE TABLE teachers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE NOT NULL,
    address TEXT,
    gender ENUM('male', 'female', 'other') NOT NULL,
    registration_number VARCHAR(100) UNIQUE NOT NULL,
    profile_photo VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_registration_number (registration_number)
);

-- Stories table
CREATE TABLE stories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image VARCHAR(255),
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    INDEX idx_teacher_id (teacher_id),
    INDEX idx_is_published (is_published)
);
-- ALTER TABLE stories 
-- ADD COLUMN story_video VARCHAR(255) NULL AFTER cover_image;

-- -- Add video generation status to stories table
-- ALTER TABLE stories 
-- ADD COLUMN generated_video VARCHAR(255) NULL,
-- ADD COLUMN video_generation_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
-- ADD COLUMN last_generated_at TIMESTAMP NULL;

-- -- Add narration audio column if not exists
-- ALTER TABLE story_pages 
-- ADD COLUMN narration_audio_url VARCHAR(255) NULL AFTER text_content;

-- Story pages table
CREATE TABLE story_pages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    story_id INT NOT NULL,
    page_number INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    text_content TEXT NOT NULL,
    narration_audio_url VARCHAR(255),
    important_notes TEXT,
    duration_seconds INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_story_page (story_id, page_number),
    INDEX idx_story_id (story_id)
);
ALTER TABLE story_pages 
MODIFY text_content LONGTEXT NOT NULL,
MODIFY important_notes LONGTEXT;

-- Quizzes table
CREATE TABLE quizzes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    story_id INT UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    time_limit INT DEFAULT 600, -- in seconds
    passing_score INT DEFAULT 60, -- percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
    INDEX idx_story_id (story_id)
);

-- Quiz questions table
CREATE TABLE quiz_questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    quiz_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type ENUM('multiple_choice', 'true_false', 'short_answer') NOT NULL,
    points INT DEFAULT 1,
    correct_answer TEXT NOT NULL,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
    INDEX idx_quiz_id (quiz_id)
);

-- Student progress table
CREATE TABLE student_progress (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    story_id INT NOT NULL,
    current_page INT DEFAULT 1,
    is_completed BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_story (student_id, story_id),
    INDEX idx_student_id (student_id),
    INDEX idx_story_id (story_id)
);

-- Student quiz attempts table
CREATE TABLE student_quiz_attempts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    quiz_id INT NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    time_taken INT NOT NULL, -- in seconds
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
    INDEX idx_student_quiz (student_id, quiz_id),
    INDEX idx_submitted_at (submitted_at)
);

-- Student quiz answers table
CREATE TABLE student_quiz_answers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    attempt_id INT NOT NULL,
    question_id INT NOT NULL,
    student_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    FOREIGN KEY (attempt_id) REFERENCES student_quiz_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE,
    INDEX idx_attempt_id (attempt_id),
    INDEX idx_question_id (question_id)
);

-- Class assignments table (which stories are assigned to which classes)
CREATE TABLE class_assignments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    story_id INT NOT NULL,
    class_level VARCHAR(50) NOT NULL,
    assigned_by INT NOT NULL, -- teacher id
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES teachers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_class_assignment (story_id, class_level),
    INDEX idx_class_level (class_level)
);

-- Audit log table
CREATE TABLE audit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- Puzzle types table
CREATE TABLE puzzle_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_data TEXT, -- Changed from JSON to TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert common puzzle types
INSERT INTO puzzle_types (name, description, template_data) VALUES
('word_search', 'Find hidden words in a grid', '{"grid_size": 10, "max_words": 10, "directions": ["horizontal", "vertical", "diagonal"]}'),
('crossword', 'Fill words based on clues', '{"grid_size": 15, "max_clues": 20}'),
('matching', 'Match items from two columns', '{"pairs": 8, "type": "image_text"}'),
('fill_blank', 'Fill in the blanks in sentences', '{"blanks": 5, "hints": true}'),
('true_false', 'Answer True or False questions', '{"questions": 6}'),
('multiple_choice', 'Choose correct answer from options', '{"questions": 5, "options": 4}'),
('sequence', 'Arrange items in correct order', '{"items": 6, "type": "text"}'),
('spot_difference', 'Find differences between two images', '{"differences": 5}'),
('memory_game', 'Match pairs of cards', '{"pairs": 8}'),
('jigsaw', 'Assemble pieces to form an image', '{"pieces": 12}');

-- Story page puzzles table
CREATE TABLE story_page_puzzles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    story_page_id INT NOT NULL,
    puzzle_type_id INT NOT NULL,
    puzzle_data TEXT NOT NULL, -- Changed from JSON to TEXT
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    time_limit INT DEFAULT 180, -- seconds
    required_score INT DEFAULT 70, -- percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_page_id) REFERENCES story_pages(id) ON DELETE CASCADE,
    FOREIGN KEY (puzzle_type_id) REFERENCES puzzle_types(id),
    UNIQUE KEY unique_page_puzzle (story_page_id),
    INDEX idx_story_page (story_page_id)
);

-- Student puzzle progress table
CREATE TABLE student_puzzle_progress (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    puzzle_id INT NOT NULL,
    attempts INT DEFAULT 0,
    best_score DECIMAL(5,2) DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (puzzle_id) REFERENCES story_page_puzzles(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_puzzle (student_id, puzzle_id),
    INDEX idx_student (student_id),
    INDEX idx_puzzle (puzzle_id)
);

-- Chat conversations (teacher <-> student)
CREATE TABLE chat_conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    student_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_teacher_student (teacher_id, student_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Chat messages
CREATE TABLE chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    sender_type ENUM('teacher','student') NOT NULL,
    sender_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation (conversation_id),
    INDEX idx_created_at (created_at)
);

-- Student-to-student chat tables (make sure these exist)
CREATE TABLE IF NOT EXISTS student_conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student1_id INT NOT NULL,
    student2_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_student_pair (student1_id, student2_id),
    FOREIGN KEY (student1_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (student2_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_student1 (student1_id),
    INDEX idx_student2 (student2_id)
);

CREATE TABLE IF NOT EXISTS student_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES student_conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_conversation (conversation_id),
    INDEX idx_sender (sender_id),
    INDEX idx_created_at (created_at),
    INDEX idx_is_read (is_read)
);