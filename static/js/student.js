// Student Portal JavaScript

class StudentDashboard {
    constructor() {
        this.initializeEventListeners();
        this.initializeProgressBars();
        this.setupStoryFilters();
        this.setupAutoRefresh();
    }
    
    initializeEventListeners() {
        // Story card interactions
        document.querySelectorAll('.story-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.btn')) {
                    const storyId = card.dataset.storyId;
                    if (storyId) {
                        window.location.href = `/student/story/${storyId}`;
                    }
                }
            });
        });
        
        // Progress bar animation
        document.querySelectorAll('.progress-fill').forEach(progress => {
            const width = progress.style.width;
            progress.style.width = '0%';
            setTimeout(() => {
                progress.style.transition = 'width 1s ease';
                progress.style.width = width;
            }, 100);
        });
        
        // Quick actions
        document.querySelectorAll('.quick-action').forEach(action => {
            action.addEventListener('click', (e) => {
                e.preventDefault();
                const actionType = action.dataset.action;
                this.handleQuickAction(actionType);
            });
        });
    }
    
    initializeProgressBars() {
        // Animate progress bars on scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const progressFill = entry.target.querySelector('.progress-fill');
                    if (progressFill) {
                        const targetWidth = progressFill.dataset.width || progressFill.style.width;
                        progressFill.style.width = '0%';
                        setTimeout(() => {
                            progressFill.style.transition = 'width 1s ease';
                            progressFill.style.width = targetWidth;
                        }, 300);
                    }
                }
            });
        }, { threshold: 0.5 });
        
        document.querySelectorAll('.progress-container').forEach(container => {
            observer.observe(container);
        });
    }
    
    setupStoryFilters() {
        const filterInput = document.getElementById('story-filter');
        const classFilter = document.getElementById('class-filter');
        const statusFilter = document.getElementById('status-filter');
        
        if (filterInput) {
            filterInput.addEventListener('input', this.filterStories.bind(this));
        }
        
        if (classFilter) {
            classFilter.addEventListener('change', this.filterStories.bind(this));
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', this.filterStories.bind(this));
        }
    }
    
    filterStories() {
        const searchTerm = document.getElementById('story-filter')?.value.toLowerCase() || '';
        const classFilter = document.getElementById('class-filter')?.value || '';
        const statusFilter = document.getElementById('status-filter')?.value || '';
        
        document.querySelectorAll('.story-card').forEach(card => {
            const title = card.querySelector('h3').textContent.toLowerCase();
            const description = card.querySelector('.story-description').textContent.toLowerCase();
            const storyClass = card.dataset.class || '';
            const isCompleted = card.dataset.completed === 'true';
            
            let matchesSearch = title.includes(searchTerm) || description.includes(searchTerm);
            let matchesClass = !classFilter || storyClass === classFilter;
            let matchesStatus = !statusFilter || 
                (statusFilter === 'completed' && isCompleted) ||
                (statusFilter === 'in-progress' && !isCompleted);
            
            if (matchesSearch && matchesClass && matchesStatus) {
                card.style.display = 'block';
                card.style.animation = 'fadeIn 0.3s ease';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    setupAutoRefresh() {
        // Refresh progress every 30 seconds
        setInterval(() => {
            this.refreshProgress();
        }, 30000);
    }
    
    async refreshProgress() {
        try {
            const response = await fetch('/api/student/progress');
            if (response.ok) {
                const progressData = await response.json();
                this.updateProgressDisplay(progressData);
            }
        } catch (error) {
            console.error('Error refreshing progress:', error);
        }
    }
    
    updateProgressDisplay(progressData) {
        progressData.forEach(progress => {
            const storyCard = document.querySelector(`.story-card[data-story-id="${progress.story_id}"]`);
            if (storyCard) {
                // Update progress bar
                const progressFill = storyCard.querySelector('.progress-fill');
                if (progressFill) {
                    const progressPercent = (progress.current_page / progress.total_pages * 100).toFixed(1);
                    progressFill.style.width = `${progressPercent}%`;
                    progressFill.dataset.width = `${progressPercent}%`;
                    
                    const progressText = storyCard.querySelector('.progress-text');
                    if (progressText) {
                        progressText.textContent = `${progressPercent}% Complete`;
                    }
                }
                
                // Update status badge
                if (progress.is_completed) {
                    storyCard.dataset.completed = 'true';
                    const badge = storyCard.querySelector('.badge');
                    if (badge) {
                        badge.className = 'badge badge-success';
                        badge.textContent = 'Completed';
                    }
                }
            }
        });
    }
    
    handleQuickAction(actionType) {
        switch(actionType) {
            case 'continue-reading':
                const firstInProgress = document.querySelector('.story-card[data-completed="false"]');
                if (firstInProgress) {
                    const storyId = firstInProgress.dataset.storyId;
                    window.location.href = `/student/story/${storyId}`;
                } else {
                    this.showNotification('No stories in progress', 'info');
                }
                break;
                
            case 'view-completed':
                window.location.href = '?status=completed';
                break;
                
            case 'take-quiz':
                const firstCompleted = document.querySelector('.story-card[data-completed="true"]');
                if (firstCompleted) {
                    const storyId = firstCompleted.dataset.storyId;
                    window.location.href = `/student/quiz/${storyId}`;
                } else {
                    this.showNotification('No completed stories with quizzes', 'warning');
                }
                break;
        }
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.student-notification');
        existingNotifications.forEach(notification => notification.remove());
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `student-notification alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;
        
        // Add to page
        document.querySelector('.container').insertBefore(notification, document.querySelector('.container').firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

class StoryViewer {
    constructor(storyId, pages, currentPage) {
        this.storyId = storyId;
        this.pages = pages;
        this.currentPage = currentPage;
        this.totalPages = pages.length;
        this.isPlaying = false;
        this.audio = null;
        this.autoPlayInterval = null;
        this.initialize();
    }
    
    initialize() {
        this.loadCurrentPage();
        this.setupEventListeners();
        this.setupKeyboardNavigation();
        this.setupTouchSwipe();
        this.startAutoSave();
    }
    
    loadCurrentPage() {
        const page = this.pages[this.currentPage - 1];
        if (!page) return;
        
        // Update image
        const imgElement = document.getElementById('story-image');
        if (imgElement && page.image_url) {
            imgElement.src = `/static/uploads/stories/${page.image_url}`;
            imgElement.alt = `Page ${this.currentPage} - ${page.text_content.substring(0, 50)}...`;
            
            // Add loading state
            imgElement.classList.add('loading');
            imgElement.onload = () => {
                imgElement.classList.remove('loading');
            };
            imgElement.onerror = () => {
                imgElement.classList.remove('loading');
                imgElement.src = '/static/images/default-story-image.jpg';
            };
        }
        
        // Update text
        const textElement = document.getElementById('story-text');
        if (textElement) {
            textElement.textContent = page.text_content;
        }
        
        // Update notes
        const notesElement = document.getElementById('story-notes');
        if (notesElement) {
            if (page.important_notes) {
                notesElement.innerHTML = `
                    <h4><i class="fas fa-lightbulb"></i> Important Notes</h4>
                    <p>${page.important_notes}</p>
                `;
                notesElement.style.display = 'block';
            } else {
                notesElement.style.display = 'none';
            }
        }
        
        // Update page indicator
        const indicator = document.getElementById('page-indicator');
        if (indicator) {
            indicator.textContent = `${this.currentPage} / ${this.totalPages}`;
        }
        
        // Update progress bar
        this.updateProgressBar();
        
        // Update navigation buttons
        this.updateNavigationButtons();
        
        // Load narration
        this.loadNarration(page.narration_audio_url);
        
        // Update browser title
        document.title = `Page ${this.currentPage} - ${document.title.split(' - ')[0]}`;
        
        // Save progress
        this.saveProgress();
    }
    
    setupEventListeners() {
        // Navigation buttons
        document.getElementById('prev-page')?.addEventListener('click', () => this.prevPage());
        document.getElementById('next-page')?.addEventListener('click', () => this.nextPage());
        
        // Auto-play toggle
        document.getElementById('auto-play')?.addEventListener('click', () => this.toggleAutoPlay());
        
        // Narration toggle
        document.getElementById('play-narration')?.addEventListener('click', () => this.toggleNarration());
        
        // Volume control
        const volumeSlider = document.getElementById('volume-slider');
        if (volumeSlider) {
            volumeSlider.addEventListener('input', (e) => {
                if (this.audio) {
                    this.audio.volume = e.target.value / 100;
                }
            });
        }
        
        // Page jump
        const pageJump = document.getElementById('page-jump');
        if (pageJump) {
            pageJump.addEventListener('change', (e) => {
                const pageNum = parseInt(e.target.value);
                if (pageNum >= 1 && pageNum <= this.totalPages) {
                    this.jumpToPage(pageNum);
                }
            });
        }
        
        // Fullscreen toggle
        document.getElementById('fullscreen-toggle')?.addEventListener('click', () => this.toggleFullscreen());
        
        // Text size controls
        document.getElementById('text-increase')?.addEventListener('click', () => this.adjustTextSize(1));
        document.getElementById('text-decrease')?.addEventListener('click', () => this.adjustTextSize(-1));
        document.getElementById('text-reset')?.addEventListener('click', () => this.resetTextSize());
    }
    
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Don't interfere with form inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch(e.key) {
                case 'ArrowLeft':
                case 'PageUp':
                    e.preventDefault();
                    this.prevPage();
                    break;
                    
                case 'ArrowRight':
                case 'PageDown':
                case ' ':
                    e.preventDefault();
                    this.nextPage();
                    break;
                    
                case 'Home':
                    e.preventDefault();
                    this.jumpToPage(1);
                    break;
                    
                case 'End':
                    e.preventDefault();
                    this.jumpToPage(this.totalPages);
                    break;
                    
                case 'a':
                case 'A':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.toggleAutoPlay();
                    }
                    break;
                    
                case 'm':
                case 'M':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.toggleNarration();
                    }
                    break;
                    
                case 'f':
                case 'F':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.toggleFullscreen();
                    }
                    break;
            }
        });
    }
    
    setupTouchSwipe() {
        let touchStartX = 0;
        let touchEndX = 0;
        
        const storyContainer = document.querySelector('.story-content');
        if (!storyContainer) return;
        
        storyContainer.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        storyContainer.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe(touchStartX, touchEndX);
        }, { passive: true });
    }
    
    handleSwipe(startX, endX) {
        const swipeThreshold = 50;
        const diff = startX - endX;
        
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                // Swipe left - next page
                this.nextPage();
            } else {
                // Swipe right - previous page
                this.prevPage();
            }
        }
    }
    
    startAutoSave() {
        // Auto-save progress every 30 seconds
        setInterval(() => {
            this.saveProgress();
        }, 30000);
        
        // Save on page unload
        window.addEventListener('beforeunload', () => {
            this.saveProgress(true);
        });
    }
    
    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadCurrentPage();
            this.animatePageTransition('prev');
        } else {
            this.showNotification('You are on the first page', 'info');
        }
    }
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadCurrentPage();
            this.animatePageTransition('next');
        } else {
            // Last page reached
            this.completeStory();
        }
    }
    
    jumpToPage(pageNumber) {
        if (pageNumber >= 1 && pageNumber <= this.totalPages) {
            this.currentPage = pageNumber;
            this.loadCurrentPage();
            this.animatePageTransition('jump');
        }
    }
    
    animatePageTransition(direction) {
        const imageContainer = document.querySelector('.story-image-container');
        if (!imageContainer) return;
        
        // Remove previous animation classes
        imageContainer.classList.remove('page-transition-prev', 'page-transition-next', 'page-transition-jump');
        
        // Force reflow
        void imageContainer.offsetWidth;
        
        // Add new animation class
        imageContainer.classList.add(`page-transition-${direction}`);
        
        // Remove animation class after animation completes
        setTimeout(() => {
            imageContainer.classList.remove(`page-transition-${direction}`);
        }, 500);
    }
    
    toggleAutoPlay() {
        const button = document.getElementById('auto-play');
        if (!button) return;
        
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
            button.innerHTML = '<i class="fas fa-play"></i> Auto-play';
            button.classList.remove('active');
            this.showNotification('Auto-play stopped', 'info');
        } else {
            const pageDuration = this.pages[this.currentPage - 1]?.duration_seconds || 10;
            this.autoPlayInterval = setInterval(() => {
                if (this.currentPage < this.totalPages) {
                    this.nextPage();
                } else {
                    this.toggleAutoPlay(); // Stop at last page
                }
            }, pageDuration * 1000);
            button.innerHTML = '<i class="fas fa-pause"></i> Stop Auto-play';
            button.classList.add('active');
            this.showNotification(`Auto-play started (${pageDuration}s per page)`, 'success');
        }
    }
    
    toggleNarration() {
        const button = document.getElementById('play-narration');
        if (!button) return;
        
        if (this.audio) {
            if (this.audio.paused) {
                this.audio.play()
                    .then(() => {
                        this.isPlaying = true;
                        button.innerHTML = '<i class="fas fa-volume-mute"></i> Stop Narration';
                        button.classList.add('active');
                    })
                    .catch(error => {
                        console.error('Error playing audio:', error);
                        this.showNotification('Error playing narration audio', 'error');
                    });
            } else {
                this.audio.pause();
                this.isPlaying = false;
                button.innerHTML = '<i class="fas fa-volume-up"></i> Play Narration';
                button.classList.remove('active');
            }
        } else {
            this.showNotification('No narration available for this page', 'warning');
        }
    }
    
    loadNarration(audioUrl) {
        // Stop current audio
        if (this.audio) {
            this.audio.pause();
            this.audio = null;
            this.isPlaying = false;
            
            // Update button
            const button = document.getElementById('play-narration');
            if (button) {
                button.innerHTML = '<i class="fas fa-volume-up"></i> Play Narration';
                button.classList.remove('active');
            }
        }
        
        // Load new audio if available
        if (audioUrl) {
            this.audio = new Audio(`/static/uploads/stories/${audioUrl}`);
            this.audio.volume = document.getElementById('volume-slider')?.value / 100 || 0.5;
            
            this.audio.addEventListener('ended', () => {
                this.isPlaying = false;
                const button = document.getElementById('play-narration');
                if (button) {
                    button.innerHTML = '<i class="fas fa-volume-up"></i> Play Narration';
                    button.classList.remove('active');
                }
            });
            
            this.audio.addEventListener('error', () => {
                this.showNotification('Error loading narration audio', 'error');
                this.audio = null;
            });
            
            // Auto-play if auto-play is enabled
            if (this.autoPlayInterval && this.isPlaying) {
                this.audio.play().catch(console.error);
            }
        }
    }
    
    toggleFullscreen() {
        const elem = document.documentElement;
        
        if (!document.fullscreenElement) {
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) { /* Safari */
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) { /* IE11 */
                elem.msRequestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) { /* Safari */
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) { /* IE11 */
                document.msExitFullscreen();
            }
        }
    }
    
    adjustTextSize(change) {
        const textElement = document.getElementById('story-text');
        if (!textElement) return;
        
        const currentSize = parseInt(window.getComputedStyle(textElement).fontSize);
        const newSize = currentSize + change;
        
        // Limit size between 14px and 24px
        if (newSize >= 14 && newSize <= 24) {
            textElement.style.fontSize = `${newSize}px`;
            
            // Save preference
            localStorage.setItem('storyTextSize', newSize);
            
            this.showNotification(`Text size: ${newSize}px`, 'info');
        }
    }
    
    resetTextSize() {
        const textElement = document.getElementById('story-text');
        if (textElement) {
            textElement.style.fontSize = '';
            localStorage.removeItem('storyTextSize');
            this.showNotification('Text size reset to default', 'success');
        }
    }
    
    updateProgressBar() {
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        
        if (progressFill) {
            const progressPercent = (this.currentPage / this.totalPages * 100).toFixed(1);
            progressFill.style.width = `${progressPercent}%`;
            
            if (progressText) {
                progressText.textContent = `${progressPercent}% Complete`;
            }
        }
    }
    
    updateNavigationButtons() {
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentPage === 1;
            prevBtn.classList.toggle('disabled', this.currentPage === 1);
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentPage === this.totalPages;
            nextBtn.classList.toggle('disabled', this.currentPage === this.totalPages);
            
            if (this.currentPage === this.totalPages) {
                nextBtn.innerHTML = '<i class="fas fa-check-circle"></i> Complete Story';
                nextBtn.classList.add('btn-success');
                nextBtn.classList.remove('btn-primary');
            } else {
                nextBtn.innerHTML = 'Next <i class="fas fa-chevron-right"></i>';
                nextBtn.classList.remove('btn-success');
                nextBtn.classList.add('btn-primary');
            }
        }
    }
    
    async saveProgress(force = false) {
        const isCompleted = this.currentPage === this.totalPages;
        
        try {
            const response = await fetch('/api/update_progress', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    story_id: this.storyId,
                    current_page: this.currentPage,
                    is_completed: isCompleted
                })
            });
            
            if (response.ok) {
                // Save locally for offline tracking
                localStorage.setItem(`story_progress_${this.storyId}`, JSON.stringify({
                    currentPage: this.currentPage,
                    isCompleted: isCompleted,
                    lastUpdated: new Date().toISOString()
                }));
                
                if (force) {
                    console.log('Progress saved successfully');
                }
            }
        } catch (error) {
            console.error('Error saving progress:', error);
            
            // Fallback: Save to localStorage
            localStorage.setItem(`story_progress_${this.storyId}`, JSON.stringify({
                currentPage: this.currentPage,
                isCompleted: isCompleted,
                lastUpdated: new Date().toISOString(),
                offline: true
            }));
        }
    }
    
    completeStory() {
        // Show completion modal
        const completionModal = document.getElementById('completion-modal');
        if (completionModal) {
            completionModal.style.display = 'block';
            
            // Auto-redirect to quiz after 5 seconds
            setTimeout(() => {
                window.location.href = `/student/quiz/${this.storyId}`;
            }, 5000);
        } else {
            // Redirect immediately if no modal
            window.location.href = `/student/quiz/${this.storyId}`;
        }
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.story-notification');
        existingNotifications.forEach(notification => notification.remove());
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `story-notification alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;
        
        // Add to page
        const container = document.querySelector('.story-viewer-container');
        if (container) {
            container.insertBefore(notification, container.firstChild);
            
            // Auto-remove after 3 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 3000);
        }
    }
}

class StudentQuiz {
    constructor(quizId, timeLimit) {
        this.quizId = quizId;
        this.timeLimit = timeLimit; // in seconds
        this.timeLeft = timeLimit;
        this.timerInterval = null;
        this.isSubmitted = false;
        this.userAnswers = {};
        this.initialize();
    }
    
    initialize() {
        this.startTimer();
        this.setupEventListeners();
        this.loadSavedAnswers();
        this.setupAutoSave();
        this.setupQuestionNavigation();
        this.setupAnswerValidation();
    }
    
    startTimer() {
        this.updateTimerDisplay();
        
        this.timerInterval = setInterval(() => {
            this.timeLeft--;
            this.updateTimerDisplay();
            
            // Show warnings
            if (this.timeLeft === 300) { // 5 minutes
                this.showTimeWarning('5 minutes remaining');
            } else if (this.timeLeft === 60) { // 1 minute
                this.showTimeWarning('1 minute remaining');
                document.getElementById('timer-display').classList.add('warning');
            } else if (this.timeLeft === 30) { // 30 seconds
                this.showTimeWarning('30 seconds remaining');
                document.getElementById('timer-display').classList.add('danger');
            } else if (this.timeLeft <= 0) {
                this.timeUp();
            }
        }, 1000);
    }
    
    updateTimerDisplay() {
        const timerDisplay = document.getElementById('timer-display');
        if (!timerDisplay) return;
        
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Update time taken input
        const timeTakenInput = document.getElementById('time-taken');
        if (timeTakenInput) {
            timeTakenInput.value = this.timeLimit - this.timeLeft;
        }
    }
    
    showTimeWarning(message) {
        // Create warning notification
        const warning = document.createElement('div');
        warning.className = 'alert alert-warning alert-dismissible fade show';
        warning.innerHTML = `
            <i class="fas fa-clock"></i>
            <strong>Time Warning:</strong> ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        // Add to page
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
    
    timeUp() {
        clearInterval(this.timerInterval);
        
        // Show timeout message
        const timeoutMessage = document.createElement('div');
        timeoutMessage.className = 'alert alert-danger';
        timeoutMessage.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Time's Up!</strong> Submitting your quiz now...
        `;
        
        const quizContainer = document.querySelector('.quiz-container');
        if (quizContainer) {
            quizContainer.insertBefore(timeoutMessage, quizContainer.firstChild);
        }
        
        // Submit form after 2 seconds
        setTimeout(() => {
            document.getElementById('quiz-form').submit();
        }, 2000);
    }
    
    setupEventListeners() {
        // Form submission
        const quizForm = document.getElementById('quiz-form');
        if (quizForm) {
            quizForm.addEventListener('submit', (e) => {
                if (!this.validateForm()) {
                    e.preventDefault();
                    return;
                }
                
                // Prevent multiple submissions
                if (this.isSubmitted) {
                    e.preventDefault();
                    return;
                }
                
                this.isSubmitted = true;
                
                // Show submitting message
                const submitButton = quizForm.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
                }
                
                // Stop timer
                clearInterval(this.timerInterval);
                
                // Clear saved answers
                localStorage.removeItem(`quiz_answers_${this.quizId}`);
            });
        }
        
        // Answer selection
        document.querySelectorAll('input[type="radio"], textarea').forEach(input => {
            input.addEventListener('change', (e) => {
                const questionId = e.target.name.replace('question_', '');
                this.userAnswers[questionId] = e.target.value;
                this.markQuestionAnswered(questionId);
                this.saveAnswers();
            });
        });
        
        // Before leaving page warning
        window.addEventListener('beforeunload', (e) => {
            if (!this.isSubmitted && Object.keys(this.userAnswers).length > 0) {
                e.preventDefault();
                e.returnValue = 'You have unsaved quiz answers. Are you sure you want to leave?';
            }
        });
    }
    
    setupQuestionNavigation() {
        const questions = document.querySelectorAll('.question-card');
        if (questions.length <= 1) return;
        
        // Create navigation if not exists
        if (!document.querySelector('.quiz-navigation')) {
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
                
                // Setup navigation event listeners
                this.setupQuestionNavEvents();
            }
        }
    }
    
    setupQuestionNavEvents() {
        // Question number buttons
        document.querySelectorAll('.question-number').forEach(button => {
            button.addEventListener('click', () => {
                const questionNum = parseInt(button.dataset.question);
                this.showQuestion(questionNum);
            });
        });
        
        // Previous button
        document.getElementById('prev-question')?.addEventListener('click', () => {
            const currentQuestion = this.getCurrentQuestion();
            if (currentQuestion > 1) {
                this.showQuestion(currentQuestion - 1);
            }
        });
        
        // Next button
        document.getElementById('next-question')?.addEventListener('click', () => {
            const currentQuestion = this.getCurrentQuestion();
            const totalQuestions = document.querySelectorAll('.question-card').length;
            if (currentQuestion < totalQuestions) {
                this.showQuestion(currentQuestion + 1);
            }
        });
    }
    
    getCurrentQuestion() {
        const activeQuestion = document.querySelector('.question-card.active');
        if (!activeQuestion) return 1;
        
        const questionNum = activeQuestion.dataset.question;
        return parseInt(questionNum) || 1;
    }
    
    showQuestion(questionNum) {
        // Hide all questions
        document.querySelectorAll('.question-card').forEach(card => {
            card.classList.remove('active');
        });
        
        // Show selected question
        const questionCard = document.querySelector(`.question-card[data-question="${questionNum}"]`);
        if (questionCard) {
            questionCard.classList.add('active');
            
            // Update navigation buttons
            this.updateQuestionNavButtons(questionNum);
            
            // Scroll to question
            questionCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    updateQuestionNavButtons(currentQuestion) {
        const totalQuestions = document.querySelectorAll('.question-card').length;
        const prevBtn = document.getElementById('prev-question');
        const nextBtn = document.getElementById('next-question');
        
        if (prevBtn) {
            prevBtn.disabled = currentQuestion === 1;
        }
        
        if (nextBtn) {
            nextBtn.disabled = currentQuestion === totalQuestions;
            nextBtn.innerHTML = currentQuestion === totalQuestions 
                ? 'Submit Quiz <i class="fas fa-paper-plane"></i>'
                : 'Next <i class="fas fa-chevron-right"></i>';
        }
        
        // Update question number buttons
        document.querySelectorAll('.question-number').forEach(button => {
            button.classList.remove('active');
            if (parseInt(button.dataset.question) === currentQuestion) {
                button.classList.add('active');
            }
        });
    }
    
    setupAnswerValidation() {
        // Real-time validation for short answers
        document.querySelectorAll('textarea').forEach(textarea => {
            textarea.addEventListener('input', (e) => {
                this.validateShortAnswer(e.target);
            });
        });
    }
    
    validateShortAnswer(textarea) {
        const value = textarea.value.trim();
        const minLength = 10; // Minimum characters for short answer
        const maxLength = 500; // Maximum characters
        
        // Remove any existing validation messages
        const existingError = textarea.parentNode.querySelector('.validation-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Validate length
        if (value.length > 0 && value.length < minLength) {
            const error = document.createElement('div');
            error.className = 'validation-error text-danger small mt-1';
            error.textContent = `Answer should be at least ${minLength} characters`;
            textarea.parentNode.appendChild(error);
            return false;
        }
        
        if (value.length > maxLength) {
            const error = document.createElement('div');
            error.className = 'validation-error text-danger small mt-1';
            error.textContent = `Answer should not exceed ${maxLength} characters`;
            textarea.parentNode.appendChild(error);
            return false;
        }
        
        return true;
    }
    
    validateForm() {
        let isValid = true;
        const questions = document.querySelectorAll('.question-card');
        
        questions.forEach((question, index) => {
            const questionId = question.querySelector('[name^="question_"]')?.name.replace('question_', '');
            if (!questionId) return;
            
            const answer = this.userAnswers[questionId];
            const isRequired = question.querySelector('[required]') !== null;
            
            if (isRequired && (!answer || answer.trim() === '')) {
                isValid = false;
                this.highlightUnanswered(question, index + 1);
            } else {
                this.removeHighlight(question);
            }
        });
        
        if (!isValid) {
            this.showNotification('Please answer all required questions', 'error');
            
            // Scroll to first unanswered question
            const firstUnanswered = document.querySelector('.question-card.unanswered');
            if (firstUnanswered) {
                firstUnanswered.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        
        return isValid;
    }
    
    highlightUnanswered(questionElement, questionNumber) {
        questionElement.classList.add('unanswered');
        
        // Add error message if not already present
        if (!questionElement.querySelector('.required-error')) {
            const error = document.createElement('div');
            error.className = 'required-error alert alert-danger mt-2';
            error.innerHTML = `<i class="fas fa-exclamation-circle"></i> This question is required`;
            questionElement.querySelector('.question-options')?.appendChild(error);
        }
        
        // Highlight in navigation
        const navButton = document.querySelector(`.question-number[data-question="${questionNumber}"]`);
        if (navButton) {
            navButton.classList.add('unanswered');
        }
    }
    
    removeHighlight(questionElement) {
        questionElement.classList.remove('unanswered');
        
        // Remove error message
        const error = questionElement.querySelector('.required-error');
        if (error) {
            error.remove();
        }
        
        // Remove from navigation
        const questionNumber = questionElement.dataset.question;
        const navButton = document.querySelector(`.question-number[data-question="${questionNumber}"]`);
        if (navButton) {
            navButton.classList.remove('unanswered');
        }
    }
    
    markQuestionAnswered(questionId) {
        const questionElement = document.querySelector(`[name="question_${questionId}"]`)?.closest('.question-card');
        if (questionElement) {
            questionElement.classList.add('answered');
            this.removeHighlight(questionElement);
            
            // Mark in navigation
            const questionNumber = questionElement.dataset.question;
            const navButton = document.querySelector(`.question-number[data-question="${questionNumber}"]`);
            if (navButton) {
                navButton.classList.add('answered');
            }
        }
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds
        setInterval(() => {
            this.saveAnswers();
        }, 30000);
        
        // Save on blur (when user leaves the page)
        window.addEventListener('blur', () => {
            this.saveAnswers();
        });
    }
    
    saveAnswers() {
        if (Object.keys(this.userAnswers).length > 0) {
            const saveData = {
                answers: this.userAnswers,
                timeLeft: this.timeLeft,
                lastSaved: new Date().toISOString()
            };
            
            localStorage.setItem(`quiz_answers_${this.quizId}`, JSON.stringify(saveData));
            
            // Show saved indicator
            this.showSaveIndicator();
        }
    }
    
    loadSavedAnswers() {
        const savedData = localStorage.getItem(`quiz_answers_${this.quizId}`);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                this.userAnswers = data.answers || {};
                
                // Restore answers
                Object.keys(this.userAnswers).forEach(questionId => {
                    const answer = this.userAnswers[questionId];
                    const input = document.querySelector(`[name="question_${questionId}"]`);
                    
                    if (input) {
                        if (input.type === 'radio') {
                            const radio = document.querySelector(`[name="question_${questionId}"][value="${answer}"]`);
                            if (radio) {
                                radio.checked = true;
                                this.markQuestionAnswered(questionId);
                            }
                        } else {
                            input.value = answer;
                            this.markQuestionAnswered(questionId);
                        }
                    }
                });
                
                // Restore timer if applicable
                if (data.timeLeft && data.timeLeft > 0) {
                    this.timeLeft = data.timeLeft;
                    this.updateTimerDisplay();
                }
                
                this.showNotification('Previous answers restored', 'success');
            } catch (error) {
                console.error('Error loading saved answers:', error);
            }
        }
    }
    
    showSaveIndicator() {
        // Remove existing indicator
        const existingIndicator = document.querySelector('.save-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        // Create new indicator
        const indicator = document.createElement('div');
        indicator.className = 'save-indicator alert alert-success';
        indicator.innerHTML = '<i class="fas fa-check"></i> Answers saved';
        indicator.style.position = 'fixed';
        indicator.style.bottom = '20px';
        indicator.style.right = '20px';
        indicator.style.zIndex = '1000';
        indicator.style.padding = '10px 20px';
        indicator.style.borderRadius = 'var(--border-radius)';
        indicator.style.boxShadow = 'var(--shadow)';
        
        document.body.appendChild(indicator);
        
        // Auto-remove after 2 seconds
        setTimeout(() => {
            if (indicator.parentElement) {
                indicator.remove();
            }
        }, 2000);
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.quiz-notification');
        existingNotifications.forEach(notification => notification.remove());
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `quiz-notification alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;
        
        // Add to page
        const container = document.querySelector('.quiz-container');
        if (container) {
            container.insertBefore(notification, container.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
    }
}

class StudentProfile {
    constructor() {
        this.initializeEventListeners();
        this.setupChartIfAvailable();
        this.setupEditMode();
        this.loadReadingStats();
    }
    
    initializeEventListeners() {
        // Profile image upload
        const profileImageInput = document.getElementById('profile-image-input');
        if (profileImageInput) {
            profileImageInput.addEventListener('change', (e) => {
                this.handleProfileImageUpload(e);
            });
        }
        
        // Edit profile button
        const editProfileBtn = document.getElementById('edit-profile-btn');
        if (editProfileBtn) {
            editProfileBtn.addEventListener('click', () => {
                this.toggleEditMode(true);
            });
        }
        
        // Save profile button
        const saveProfileBtn = document.getElementById('save-profile-btn');
        if (saveProfileBtn) {
            saveProfileBtn.addEventListener('click', () => {
                this.saveProfile();
            });
        }
        
        // Cancel edit button
        const cancelEditBtn = document.getElementById('cancel-edit-btn');
        if (cancelEditBtn) {
            cancelEditBtn.addEventListener('click', () => {
                this.toggleEditMode(false);
            });
        }
        
        // Export data button
        const exportDataBtn = document.getElementById('export-data-btn');
        if (exportDataBtn) {
            exportDataBtn.addEventListener('click', () => {
                this.exportProfileData();
            });
        }
    }
    
    setupChartIfAvailable() {
        // Check if Chart.js is available and we have quiz data
        const quizChartCanvas = document.getElementById('quiz-performance-chart');
        if (quizChartCanvas && typeof Chart !== 'undefined') {
            this.createQuizPerformanceChart();
        }
        
        const readingChartCanvas = document.getElementById('reading-progress-chart');
        if (readingChartCanvas && typeof Chart !== 'undefined') {
            this.createReadingProgressChart();
        }
    }
    
    createQuizPerformanceChart() {
        const ctx = document.getElementById('quiz-performance-chart').getContext('2d');
        const quizScores = JSON.parse(document.getElementById('quiz-scores-data')?.textContent || '[]');
        
        if (quizScores.length === 0) return;
        
        const labels = quizScores.map(score => score.story_title.substring(0, 15) + '...');
        const scores = quizScores.map(score => score.score);
        const passingScore = quizScores[0]?.passing_score || 60;
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Quiz Scores',
                    data: scores,
                    borderColor: '#4a6fa5',
                    backgroundColor: 'rgba(74, 111, 165, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Passing Score',
                    data: Array(labels.length).fill(passingScore),
                    borderColor: '#28a745',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Score (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Quizzes'
                        }
                    }
                }
            }
        });
    }
    
    createReadingProgressChart() {
        const ctx = document.getElementById('reading-progress-chart').getContext('2d');
        const readingData = JSON.parse(document.getElementById('reading-data')?.textContent || '[]');
        
        if (readingData.length === 0) return;
        
        const labels = readingData.map(item => item.month);
        const completed = readingData.map(item => item.completed);
        const started = readingData.map(item => item.started);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Completed',
                    data: completed,
                    backgroundColor: '#28a745'
                }, {
                    label: 'Started',
                    data: started,
                    backgroundColor: '#4a6fa5'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Stories'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month'
                        }
                    }
                }
            }
        });
    }
    
    setupEditMode() {
        // Check if we're in edit mode from URL
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('edit') === 'true') {
            this.toggleEditMode(true);
        }
    }
    
    toggleEditMode(enable) {
        const viewMode = document.getElementById('profile-view-mode');
        const editMode = document.getElementById('profile-edit-mode');
        
        if (viewMode && editMode) {
            if (enable) {
                viewMode.style.display = 'none';
                editMode.style.display = 'block';
                
                // Update URL without reloading
                const url = new URL(window.location);
                url.searchParams.set('edit', 'true');
                window.history.pushState({}, '', url);
            } else {
                viewMode.style.display = 'block';
                editMode.style.display = 'none';
                
                // Remove edit parameter from URL
                const url = new URL(window.location);
                url.searchParams.delete('edit');
                window.history.pushState({}, '', url);
            }
        }
    }
    
    async handleProfileImageUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file
        if (!file.type.startsWith('image/')) {
            this.showNotification('Please select an image file', 'error');
            return;
        }
        
        if (file.size > 5 * 1024 * 1024) { // 5MB
            this.showNotification('Image must be less than 5MB', 'error');
            return;
        }
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.getElementById('profile-image-preview');
            if (preview) {
                preview.src = e.target.result;
            }
        };
        reader.readAsDataURL(file);
        
        // Upload to server
        const formData = new FormData();
        formData.append('profile_image', file);
        
        try {
            const response = await fetch('/api/student/update_profile_image', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.showNotification('Profile image updated successfully', 'success');
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            console.error('Error uploading profile image:', error);
            this.showNotification('Failed to update profile image', 'error');
        }
    }
    
    async saveProfile() {
        const form = document.getElementById('profile-edit-form');
        if (!form) return;
        
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/api/student/update_profile', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showNotification('Profile updated successfully', 'success');
                
                // Update display fields
                this.updateProfileDisplay(data);
                
                // Switch back to view mode
                setTimeout(() => {
                    this.toggleEditMode(false);
                    location.reload(); // Refresh to show updated data
                }, 1000);
            } else {
                throw new Error('Update failed');
            }
        } catch (error) {
            console.error('Error updating profile:', error);
            this.showNotification('Failed to update profile', 'error');
        }
    }
    
    updateProfileDisplay(profileData) {
        // Update profile header
        const nameElement = document.querySelector('.profile-info h1');
        if (nameElement && profileData.first_name && profileData.last_name) {
            nameElement.textContent = `${profileData.first_name} ${profileData.last_name}`;
        }
        
        // Update email
        const emailElement = document.querySelector('.profile-email');
        if (emailElement && profileData.email) {
            emailElement.textContent = profileData.email;
        }
        
        // Update class level badge
        const classBadge = document.querySelector('.badge-primary');
        if (classBadge && profileData.class_level) {
            classBadge.innerHTML = `<i class="fas fa-graduation-cap"></i> ${profileData.class_level}`;
        }
    }
    
    async loadReadingStats() {
        try {
            const response = await fetch('/api/student/reading_stats');
            if (response.ok) {
                const stats = await response.json();
                this.updateReadingStatsDisplay(stats);
            }
        } catch (error) {
            console.error('Error loading reading stats:', error);
        }
    }
    
    updateReadingStatsDisplay(stats) {
        // Update stats cards
        const completedStories = document.querySelector('.stat-card:nth-child(1) h3');
        const totalStories = document.querySelector('.stat-card:nth-child(2) h3');
        const avgScore = document.querySelector('.stat-card:nth-child(3) h3');
        
        if (completedStories && stats.completed_stories !== undefined) {
            completedStories.textContent = stats.completed_stories;
        }
        
        if (totalStories && stats.total_stories_read !== undefined) {
            totalStories.textContent = stats.total_stories_read;
        }
        
        if (avgScore && stats.avg_quiz_score !== undefined) {
            avgScore.textContent = `${stats.avg_quiz_score}%`;
        }
        
        // Update progress bars
        const completionRate = stats.total_stories_read > 0 
            ? (stats.completed_stories / stats.total_stories_read * 100).toFixed(1)
            : 0;
        
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${completionRate}%`;
            
            const progressText = document.querySelector('.progress-text');
            if (progressText) {
                progressText.textContent = `${completionRate}% Completion Rate`;
            }
        }
    }
    
    async exportProfileData() {
        try {
            const response = await fetch('/api/student/export_data');
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `student_data_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('Data exported successfully', 'success');
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Error exporting data:', error);
            this.showNotification('Failed to export data', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.profile-notification');
        existingNotifications.forEach(notification => notification.remove());
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `profile-notification alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;
        
        // Add to page
        const container = document.querySelector('.profile-container');
        if (container) {
            container.insertBefore(notification, container.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
    }
}

// Initialize student dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize based on current page
    const path = window.location.pathname;
    
    if (path.includes('/student/dashboard')) {
        window.studentDashboard = new StudentDashboard();
    } 
    else if (path.includes('/student/story/')) {
        const storyData = JSON.parse(document.getElementById('story-data')?.textContent || '{}');
        if (storyData.id && storyData.pages && storyData.currentPage) {
            window.storyViewer = new StoryViewer(
                storyData.id,
                storyData.pages,
                storyData.currentPage
            );
        }
    }
    else if (path.includes('/student/quiz/')) {
        const quizData = JSON.parse(document.getElementById('quiz-data')?.textContent || '{}');
        if (quizData.id && quizData.time_limit) {
            window.studentQuiz = new StudentQuiz(quizData.id, quizData.time_limit);
        }
    }
    else if (path.includes('/student/profile')) {
        window.studentProfile = new StudentProfile();
    }
    
    // Add global student functions
    window.studentFunctions = {
        toggleTheme: function() {
            const currentTheme = localStorage.getItem('theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            this.showNotification(`Switched to ${newTheme} theme`, 'success');
        },
        
        setReadingGoal: function() {
            const goal = prompt('Set your monthly reading goal (number of stories):', '5');
            if (goal && !isNaN(goal) && goal > 0) {
                localStorage.setItem('readingGoal', goal);
                this.showNotification(`Reading goal set to ${goal} stories per month`, 'success');
            }
        },
        
        showNotification: function(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `global-notification alert alert-${type}`;
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                ${message}
                <button type="button" class="close" onclick="this.parentElement.remove()">
                    <span>&times;</span>
                </button>
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
    };
});