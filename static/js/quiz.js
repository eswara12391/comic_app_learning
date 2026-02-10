// Quiz specific functionality

class QuizTimer {
    constructor(timeLimit, displayElement) {
        this.timeLimit = timeLimit; // in seconds
        this.timeLeft = timeLimit;
        this.displayElement = displayElement;
        this.timerInterval = null;
        this.isRunning = false;
    }
    
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.updateDisplay();
        
        this.timerInterval = setInterval(() => {
            this.timeLeft--;
            this.updateDisplay();
            
            if (this.timeLeft <= 0) {
                this.stop();
                this.onTimeUp?.();
            }
            
            // Warning when less than 1 minute remaining
            if (this.timeLeft === 60) {
                this.showWarning();
            }
        }, 1000);
    }
    
    stop() {
        if (!this.isRunning) return;
        
        clearInterval(this.timerInterval);
        this.isRunning = false;
    }
    
    updateDisplay() {
        if (!this.displayElement) return;
        
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        this.displayElement.textContent = 
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Update color based on time left
        if (this.timeLeft < 60) {
            this.displayElement.style.color = '#dc3545'; // Red for less than 1 minute
        } else if (this.timeLeft < 180) {
            this.displayElement.style.color = '#ffc107'; // Yellow for less than 3 minutes
        } else {
            this.displayElement.style.color = ''; // Default color
        }
    }
    
    showWarning() {
        // Create warning message
        const warning = document.createElement('div');
        warning.className = 'alert alert-warning alert-dismissible fade show';
        warning.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Time Warning:</strong> Only 1 minute remaining!
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        // Insert at the top of the quiz container
        const quizContainer = document.querySelector('.quiz-container');
        if (quizContainer) {
            quizContainer.insertBefore(warning, quizContainer.firstChild);
            
            // Auto-dismiss after 10 seconds
            setTimeout(() => {
                warning.classList.remove('show');
                setTimeout(() => warning.remove(), 300);
            }, 10000);
        }
    }
}

class QuizManager {
    constructor() {
        this.currentQuestion = 1;
        this.totalQuestions = 0;
        this.userAnswers = {};
        this.quizTimer = null;
        this.initialize();
    }
    
    initialize() {
        this.setupQuestionNavigation();
        this.setupAnswerTracking();
        this.setupTimer();
        this.setupAutoSave();
    }
    
    setupQuestionNavigation() {
        // Previous button
        const prevBtn = document.getElementById('prev-question');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.navigateToQuestion(this.currentQuestion - 1));
        }
        
        // Next button
        const nextBtn = document.getElementById('next-question');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.navigateToQuestion(this.currentQuestion + 1));
        }
        
        // Question numbers
        const questionNumbers = document.querySelectorAll('.question-number');
        questionNumbers.forEach((number, index) => {
            number.addEventListener('click', () => this.navigateToQuestion(index + 1));
        });
        
        this.totalQuestions = document.querySelectorAll('.question-card').length;
        this.updateNavigation();
    }
    
    setupAnswerTracking() {
        // Track radio button changes
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const questionId = e.target.name.replace('question_', '');
                this.userAnswers[questionId] = e.target.value;
                this.markQuestionAnswered(questionId);
                this.saveProgress();
            });
        });
        
        // Track textarea changes
        document.querySelectorAll('textarea').forEach(textarea => {
            textarea.addEventListener('input', (e) => {
                const questionId = e.target.name.replace('question_', '');
                this.userAnswers[questionId] = e.target.value;
                if (e.target.value.trim()) {
                    this.markQuestionAnswered(questionId);
                }
                this.saveProgress();
            });
        });
        
        // Load saved answers
        this.loadProgress();
    }
    
    setupTimer() {
        const timeLimit = parseInt(document.getElementById('quiz-time-limit')?.value) || 600;
        const timerDisplay = document.getElementById('timer-display');
        
        if (timerDisplay) {
            this.quizTimer = new QuizTimer(timeLimit, timerDisplay);
            this.quizTimer.onTimeUp = () => {
                alert('Time is up! Submitting your quiz...');
                document.getElementById('quiz-form').submit();
            };
            
            // Start timer when user starts interacting
            document.addEventListener('click', () => {
                if (!this.quizTimer.isRunning) {
                    this.quizTimer.start();
                }
            }, { once: true });
        }
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds
        setInterval(() => this.saveProgress(), 30000);
        
        // Save on page unload
        window.addEventListener('beforeunload', (e) => {
            if (Object.keys(this.userAnswers).length > 0) {
                this.saveProgress();
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }
    
    navigateToQuestion(questionNumber) {
        if (questionNumber < 1 || questionNumber > this.totalQuestions) return;
        
        // Hide current question
        document.getElementById(`question-${this.currentQuestion}`).classList.remove('active');
        
        // Show new question
        document.getElementById(`question-${questionNumber}`).classList.add('active');
        
        // Update current question
        this.currentQuestion = questionNumber;
        
        // Update navigation
        this.updateNavigation();
        
        // Scroll to question
        document.getElementById(`question-${questionNumber}`).scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
    
    updateNavigation() {
        const prevBtn = document.getElementById('prev-question');
        const nextBtn = document.getElementById('next-question');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentQuestion === 1;
        }
        
        if (nextBtn) {
            nextBtn.textContent = this.currentQuestion === this.totalQuestions ? 'Submit' : 'Next';
            if (this.currentQuestion === this.totalQuestions) {
                nextBtn.classList.add('btn-success');
                nextBtn.classList.remove('btn-primary');
                nextBtn.onclick = () => document.getElementById('quiz-form').submit();
            } else {
                nextBtn.classList.remove('btn-success');
                nextBtn.classList.add('btn-primary');
                nextBtn.onclick = () => this.navigateToQuestion(this.currentQuestion + 1);
            }
        }
        
        // Update question numbers
        document.querySelectorAll('.question-number').forEach((number, index) => {
            number.classList.remove('active', 'answered');
            if (index + 1 === this.currentQuestion) {
                number.classList.add('active');
            }
            if (this.userAnswers[(index + 1).toString()]) {
                number.classList.add('answered');
            }
        });
    }
    
    markQuestionAnswered(questionId) {
        const questionNumber = document.querySelector(`.question-number[data-question="${questionId}"]`);
        if (questionNumber) {
            questionNumber.classList.add('answered');
        }
    }
    
    saveProgress() {
        const progress = {
            answers: this.userAnswers,
            currentQuestion: this.currentQuestion,
            timeLeft: this.quizTimer?.timeLeft || 0,
            timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('quizProgress', JSON.stringify(progress));
    }
    
    loadProgress() {
        const savedProgress = localStorage.getItem('quizProgress');
        if (savedProgress) {
            const progress = JSON.parse(savedProgress);
            this.userAnswers = progress.answers || {};
            this.currentQuestion = progress.currentQuestion || 1;
            
            // Restore answers
            Object.keys(this.userAnswers).forEach(questionId => {
                const answer = this.userAnswers[questionId];
                const input = document.querySelector(`[name="question_${questionId}"]`);
                
                if (input) {
                    if (input.type === 'radio') {
                        const radio = document.querySelector(`[name="question_${questionId}"][value="${answer}"]`);
                        if (radio) radio.checked = true;
                    } else {
                        input.value = answer;
                    }
                    this.markQuestionAnswered(questionId);
                }
            });
            
            // Navigate to saved question
            this.navigateToQuestion(this.currentQuestion);
            
            // Restore timer if available
            if (progress.timeLeft && this.quizTimer) {
                this.quizTimer.timeLeft = progress.timeLeft;
                this.quizTimer.updateDisplay();
            }
        }
    }
    
    calculateScore() {
        let score = 0;
        let totalPoints = 0;
        
        // This would typically be calculated server-side
        // This is just for client-side estimation
        
        return {
            score,
            totalPoints,
            percentage: totalPoints > 0 ? (score / totalPoints) * 100 : 0
        };
    }
}

// Initialize quiz manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on quiz pages
    if (document.querySelector('.quiz-container')) {
        window.quizManager = new QuizManager();
    }
    
    // Add question numbering
    const questions = document.querySelectorAll('.question-card');
    questions.forEach((question, index) => {
        const header = question.querySelector('.question-header h3');
        if (header) {
            header.textContent = `Question ${index + 1}`;
        }
        
        // Add question ID
        question.id = `question-${index + 1}`;
        
        // Add active class to first question
        if (index === 0) {
            question.classList.add('active');
        }
    });
    
    // Add navigation if there are multiple questions
    if (questions.length > 1) {
        const navigation = document.createElement('div');
        navigation.className = 'quiz-navigation';
        navigation.innerHTML = `
            <div class="question-numbers">
                ${Array.from({length: questions.length}, (_, i) => 
                    `<button class="question-number" data-question="${i + 1}">${i + 1}</button>`
                ).join('')}
            </div>
            <div class="navigation-buttons">
                <button id="prev-question" class="btn btn-outline">
                    <i class="fas fa-chevron-left"></i> Previous
                </button>
                <button id="next-question" class="btn btn-primary">
                    Next <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
        
        const quizContainer = document.querySelector('.quiz-container');
        const questionsContainer = document.querySelector('.questions-container');
        if (quizContainer && questionsContainer) {
            quizContainer.insertBefore(navigation, questionsContainer);
        }
    }
    
    // Add styles for navigation
    const style = document.createElement('style');
    style.textContent = `
        .quiz-navigation {
            margin-bottom: 2rem;
        }
        
        .question-numbers {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
            justify-content: center;
        }
        
        .question-number {
            width: 40px;
            height: 40px;
            border: 2px solid var(--border-color);
            border-radius: 50%;
            background: var(--white);
            color: var(--gray);
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
        }
        
        .question-number:hover {
            border-color: var(--primary-color);
            color: var(--primary-color);
        }
        
        .question-number.active {
            background: var(--primary-color);
            border-color: var(--primary-color);
            color: var(--white);
        }
        
        .question-number.answered {
            background: var(--success-color);
            border-color: var(--success-color);
            color: var(--white);
        }
        
        .navigation-buttons {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
        }
        
        .question-card {
            display: none;
        }
        
        .question-card.active {
            display: block;
        }
    `;
    document.head.appendChild(style);
});