// // Main JavaScript file for common functionality

// document.addEventListener('DOMContentLoaded', function() {
//     // Auto-dismiss alerts after 5 seconds
//     const alerts = document.querySelectorAll('.alert');
//     alerts.forEach(alert => {
//         setTimeout(() => {
//             alert.style.transition = 'opacity 0.5s ease';
//             alert.style.opacity = '0';
//             setTimeout(() => {
//                 alert.remove();
//             }, 500);
//         }, 5000);
//     });

//     // Form validation
//     const forms = document.querySelectorAll('form[novalidate]');
//     forms.forEach(form => {
//         form.addEventListener('submit', function(e) {
//             if (!this.checkValidity()) {
//                 e.preventDefault();
//                 e.stopPropagation();
                
//                 // Add validation styling
//                 const inputs = this.querySelectorAll('input, textarea, select');
//                 inputs.forEach(input => {
//                     if (!input.validity.valid) {
//                         input.classList.add('is-invalid');
//                     } else {
//                         input.classList.remove('is-invalid');
//                     }
//                 });
                
//                 // Show first invalid field
//                 const firstInvalid = this.querySelector('.is-invalid');
//                 if (firstInvalid) {
//                     firstInvalid.focus();
//                 }
//             }
//         });
//     });

//     // Remove invalid class on input
//     document.addEventListener('input', function(e) {
//         if (e.target.classList.contains('is-invalid')) {
//             e.target.classList.remove('is-invalid');
//         }
//     });

//     // File input preview
//     const fileInputs = document.querySelectorAll('input[type="file"][accept^="image"]');
//     fileInputs.forEach(input => {
//         input.addEventListener('change', function(e) {
//             const file = e.target.files[0];
//             if (file) {
//                 // Check file size (max 5MB)
//                 if (file.size > 5 * 1024 * 1024) {
//                     alert('File size must be less than 5MB');
//                     this.value = '';
//                     return;
//                 }
                
//                 // Check file type
//                 const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
//                 if (!allowedTypes.includes(file.type)) {
//                     alert('Only JPG, PNG, GIF, and WebP images are allowed');
//                     this.value = '';
//                     return;
//                 }
                
//                 // Create preview
//                 const reader = new FileReader();
//                 reader.onload = function(e) {
//                     const preview = document.createElement('img');
//                     preview.src = e.target.result;
//                     preview.style.maxWidth = '100%';
//                     preview.style.maxHeight = '200px';
                    
//                     const parent = input.parentNode;
//                     const existingPreview = parent.querySelector('.file-preview');
//                     if (existingPreview) {
//                         existingPreview.remove();
//                     }
                    
//                     const previewDiv = document.createElement('div');
//                     previewDiv.className = 'file-preview';
//                     previewDiv.appendChild(preview);
//                     parent.appendChild(previewDiv);
//                 };
//                 reader.readAsDataURL(file);
//             }
//         });
//     });

//     // Confirm delete actions
//     const deleteForms = document.querySelectorAll('.delete-form');
//     deleteForms.forEach(form => {
//         form.addEventListener('submit', function(e) {
//             if (!confirm('Are you sure you want to delete this item?')) {
//                 e.preventDefault();
//             }
//         });
//     });

//     // Toggle password visibility
//     const togglePasswordBtns = document.querySelectorAll('.toggle-password');
//     togglePasswordBtns.forEach(btn => {
//         btn.addEventListener('click', function() {
//             const input = this.previousElementSibling;
//             const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
//             input.setAttribute('type', type);
            
//             // Toggle icon
//             const icon = this.querySelector('i');
//             if (type === 'password') {
//                 icon.classList.remove('fa-eye-slash');
//                 icon.classList.add('fa-eye');
//             } else {
//                 icon.classList.remove('fa-eye');
//                 icon.classList.add('fa-eye-slash');
//             }
//         });
//     });

//     // Search functionality
//     const searchInputs = document.querySelectorAll('[data-search]');
//     searchInputs.forEach(input => {
//         input.addEventListener('input', function() {
//             const searchTerm = this.value.toLowerCase();
//             const targetSelector = this.dataset.target;
//             const items = document.querySelectorAll(targetSelector);
            
//             items.forEach(item => {
//                 const text = item.textContent.toLowerCase();
//                 if (text.includes(searchTerm)) {
//                     item.style.display = '';
//                 } else {
//                     item.style.display = 'none';
//                 }
//             });
//         });
//     });

//     // Smooth scrolling for anchor links
//     document.querySelectorAll('a[href^="#"]').forEach(anchor => {
//         anchor.addEventListener('click', function(e) {
//             const href = this.getAttribute('href');
//             if (href === '#') return;
            
//             e.preventDefault();
//             const target = document.querySelector(href);
//             if (target) {
//                 target.scrollIntoView({
//                     behavior: 'smooth',
//                     block: 'start'
//                 });
//             }
//         });
//     });

//     // Copy to clipboard
//     const copyButtons = document.querySelectorAll('[data-copy]');
//     copyButtons.forEach(button => {
//         button.addEventListener('click', function() {
//             const textToCopy = this.dataset.copy;
//             navigator.clipboard.writeText(textToCopy).then(() => {
//                 const originalText = this.innerHTML;
//                 this.innerHTML = '<i class="fas fa-check"></i> Copied!';
//                 setTimeout(() => {
//                     this.innerHTML = originalText;
//                 }, 2000);
//             });
//         });
//     });

//     // Tooltips
//     const tooltipElements = document.querySelectorAll('[title]');
//     tooltipElements.forEach(el => {
//         el.addEventListener('mouseenter', function(e) {
//             const tooltip = document.createElement('div');
//             tooltip.className = 'tooltip';
//             tooltip.textContent = this.title;
//             document.body.appendChild(tooltip);
            
//             const rect = this.getBoundingClientRect();
//             tooltip.style.position = 'fixed';
//             tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
//             tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
            
//             this._tooltip = tooltip;
//         });
        
//         el.addEventListener('mouseleave', function() {
//             if (this._tooltip) {
//                 this._tooltip.remove();
//                 delete this._tooltip;
//             }
//         });
//     });

//     // Auto-save forms
//     const autoSaveForms = document.querySelectorAll('[data-autosave]');
//     autoSaveForms.forEach(form => {
//         let saveTimeout;
        
//         const saveForm = () => {
//             const formData = new FormData(form);
//             const data = Object.fromEntries(formData);
            
//             // Save to localStorage
//             localStorage.setItem(form.dataset.autosave, JSON.stringify(data));
            
//             // Show saved indicator
//             const indicator = document.createElement('div');
//             indicator.className = 'autosave-indicator';
//             indicator.textContent = 'Saved';
//             indicator.style.position = 'fixed';
//             indicator.style.bottom = '20px';
//             indicator.style.right = '20px';
//             indicator.style.padding = '10px 20px';
//             indicator.style.background = 'var(--success-color)';
//             indicator.style.color = 'white';
//             indicator.style.borderRadius = 'var(--border-radius)';
//             indicator.style.zIndex = '1000';
            
//             document.body.appendChild(indicator);
//             setTimeout(() => indicator.remove(), 2000);
//         };
        
//         form.addEventListener('input', () => {
//             clearTimeout(saveTimeout);
//             saveTimeout = setTimeout(saveForm, 2000);
//         });
        
//         // Load saved data
//         const savedData = localStorage.getItem(form.dataset.autosave);
//         if (savedData) {
//             const data = JSON.parse(savedData);
//             Object.keys(data).forEach(key => {
//                 const input = form.querySelector(`[name="${key}"]`);
//                 if (input) {
//                     if (input.type === 'checkbox') {
//                         input.checked = data[key] === 'on';
//                     } else {
//                         input.value = data[key];
//                     }
//                 }
//             });
//         }
//     });

//     // Responsive table
//     const tables = document.querySelectorAll('.table-responsive table');
//     tables.forEach(table => {
//         const wrapper = table.parentNode;
//         if (wrapper.offsetWidth < table.offsetWidth) {
//             wrapper.style.overflowX = 'auto';
//         }
//     });

//     // Lazy loading images
//     if ('IntersectionObserver' in window) {
//         const imageObserver = new IntersectionObserver((entries, observer) => {
//             entries.forEach(entry => {
//                 if (entry.isIntersecting) {
//                     const img = entry.target;
//                     img.src = img.dataset.src;
//                     img.classList.remove('lazy');
//                     observer.unobserve(img);
//                 }
//             });
//         });

//         document.querySelectorAll('img.lazy').forEach(img => {
//             imageObserver.observe(img);
//         });
//     }

//     // Initialize all tooltips
//     $('[data-toggle="tooltip"]').tooltip();
// });

// // Utility functions
// function formatDate(dateString) {
//     const date = new Date(dateString);
//     return date.toLocaleDateString('en-US', {
//         year: 'numeric',
//         month: 'short',
//         day: 'numeric'
//     });
// }

// function formatTime(dateString) {
//     const date = new Date(dateString);
//     return date.toLocaleTimeString('en-US', {
//         hour: '2-digit',
//         minute: '2-digit'
//     });
// }

// function debounce(func, wait) {
//     let timeout;
//     return function executedFunction(...args) {
//         const later = () => {
//             clearTimeout(timeout);
//             func(...args);
//         };
//         clearTimeout(timeout);
//         timeout = setTimeout(later, wait);
//     };
// }

// function throttle(func, limit) {
//     let inThrottle;
//     return function() {
//         const args = arguments;
//         const context = this;
//         if (!inThrottle) {
//             func.apply(context, args);
//             inThrottle = true;
//             setTimeout(() => inThrottle = false, limit);
//         }
//     };
// }

// Main JavaScript file for common functionality

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    
                    // Create error message if not exists
                    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                        const error = document.createElement('div');
                        error.className = 'invalid-feedback';
                        error.textContent = 'This field is required';
                        field.parentNode.appendChild(error);
                    }
                } else {
                    field.classList.remove('is-invalid');
                    const error = field.nextElementSibling;
                    if (error && error.classList.contains('invalid-feedback')) {
                        error.remove();
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                e.stopPropagation();
                
                // Show first invalid field
                const firstInvalid = this.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
        });
    });

    // Remove invalid class on input
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('is-invalid')) {
            e.target.classList.remove('is-invalid');
            const error = e.target.nextElementSibling;
            if (error && error.classList.contains('invalid-feedback')) {
                error.remove();
            }
        }
    });

    // File input preview
    const fileInputs = document.querySelectorAll('input[type="file"][accept^="image"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    alert('File size must be less than 5MB');
                    this.value = '';
                    return;
                }
                
                // Check file type
                const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Only JPG, PNG, GIF, and WebP images are allowed');
                    this.value = '';
                    return;
                }
                
                // Create preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.createElement('img');
                    preview.src = e.target.result;
                    preview.style.maxWidth = '100%';
                    preview.style.maxHeight = '200px';
                    
                    const parent = input.parentNode;
                    const existingPreview = parent.querySelector('.file-preview');
                    if (existingPreview) {
                        existingPreview.remove();
                    }
                    
                    const previewDiv = document.createElement('div');
                    previewDiv.className = 'file-preview mt-2';
                    previewDiv.appendChild(preview);
                    parent.appendChild(previewDiv);
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Confirm delete actions
    const deleteForms = document.querySelectorAll('form[action*="delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Toggle password visibility
    const togglePasswordBtns = document.querySelectorAll('.toggle-password');
    togglePasswordBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            
            // Toggle icon
            const icon = this.querySelector('i');
            if (type === 'password') {
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            } else {
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            }
        });
    });

    // Tab functionality
    const tabHeaders = document.querySelectorAll('.tab-header');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            // Remove active class from all tabs
            tabHeaders.forEach(h => h.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // Modal functionality
    const modalTriggers = document.querySelectorAll('[data-toggle="modal"]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.dataset.target;
            const modal = document.querySelector(modalId);
            if (modal) {
                modal.style.display = 'block';
            }
        });
    });

    const closeModalBtns = document.querySelectorAll('.close, [data-dismiss="modal"]');
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });

    // Story progress update
    const storyViewer = document.querySelector('.story-viewer-container');
    if (storyViewer) {
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', function() {
                updateStoryProgress(-1);
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', function() {
                updateStoryProgress(1);
            });
        }
        
        function updateStoryProgress(direction) {
            const currentPage = parseInt(document.getElementById('page-indicator').textContent.match(/\d+/)[0]);
            const totalPages = parseInt(document.getElementById('page-indicator').textContent.match(/\d+/g)[1]);
            const storyId = document.getElementById('story-data') ? 
                JSON.parse(document.getElementById('story-data').textContent).id : null;
            
            if (storyId) {
                const newPage = currentPage + direction;
                if (newPage >= 1 && newPage <= totalPages) {
                    fetch('/api/update_progress', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            story_id: storyId,
                            current_page: newPage,
                            is_completed: newPage === totalPages
                        })
                    }).then(response => response.json());
                }
            }
        }
    }

    // Quiz timer
    const quizTimer = document.getElementById('timer-display');
    if (quizTimer) {
        let timeLeft = parseInt(quizTimer.dataset.time) || 600;
        const timerInterval = setInterval(() => {
            timeLeft--;
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            quizTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            // Update hidden input
            const timeTakenInput = document.getElementById('time-taken');
            if (timeTakenInput) {
                const initialTime = parseInt(timeTakenInput.dataset.initial) || 600;
                timeTakenInput.value = initialTime - timeLeft;
            }
            
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                alert('Time is up! Submitting your quiz...');
                document.getElementById('quiz-form').submit();
            }
        }, 1000);
    }
});

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}