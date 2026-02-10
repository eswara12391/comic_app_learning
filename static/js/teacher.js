// Teacher Portal JavaScript

class TeacherDashboard {
    constructor() {
        this.initializeEventListeners();
        this.setupRealTimeUpdates();
        this.initializeCharts();
        this.setupQuickActions();
        this.loadNotifications();
    }
    
    initializeEventListeners() {
        // Quick stat cards
        document.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const action = card.dataset.action;
                if (action) {
                    this.handleStatCardAction(action);
                }
            });
        });
        
        // Recent activity items
        document.querySelectorAll('.recent-activity .list-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.btn')) {
                    const studentId = item.dataset.studentId;
                    const storyId = item.dataset.storyId;
                    if (studentId && storyId) {
                        window.location.href = `/teacher/students/${studentId}?story=${storyId}`;
                    }
                }
            });
        });
        
        // Quick action buttons
        document.querySelectorAll('.quick-action').forEach(action => {
            action.addEventListener('click', (e) => {
                e.preventDefault();
                const actionType = action.dataset.action;
                this.handleQuickAction(actionType);
            });
        });
        
        // Notification bell
        const notificationBell = document.getElementById('notification-bell');
        if (notificationBell) {
            notificationBell.addEventListener('click', () => {
                this.toggleNotificationsPanel();
            });
        }
        
        // Mark all as read
        const markAllReadBtn = document.getElementById('mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                this.markAllNotificationsAsRead();
            });
        }
    }
    
    setupRealTimeUpdates() {
        // Poll for updates every 30 seconds
        setInterval(() => {
            this.checkForUpdates();
        }, 30000);
        
        // Setup WebSocket if available
        this.setupWebSocket();
    }
    
    setupWebSocket() {
        if ('WebSocket' in window) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/teacher`;
            
            try {
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                };
                
                this.ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                };
                
                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    // Attempt to reconnect after 5 seconds
                    setTimeout(() => this.setupWebSocket(), 5000);
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };
            } catch (error) {
                console.error('Failed to setup WebSocket:', error);
            }
        }
    }
    
    handleWebSocketMessage(data) {
        switch(data.type) {
            case 'student_progress':
                this.updateStudentProgress(data.data);
                break;
            case 'quiz_submitted':
                this.handleNewQuizSubmission(data.data);
                break;
            case 'new_student':
                this.handleNewStudent(data.data);
                break;
            case 'notification':
                this.showNotification(data.data.message, data.data.type);
                break;
        }
    }
    
    async checkForUpdates() {
        try {
            const response = await fetch('/api/teacher/dashboard_updates');
            if (response.ok) {
                const updates = await response.json();
                this.applyUpdates(updates);
            }
        } catch (error) {
            console.error('Error checking for updates:', error);
        }
    }
    
    applyUpdates(updates) {
        // Update stats
        if (updates.stats) {
            this.updateStats(updates.stats);
        }
        
        // Update recent activity
        if (updates.recent_activity && updates.recent_activity.length > 0) {
            this.updateRecentActivity(updates.recent_activity);
        }
        
        // Update notifications
        if (updates.notifications && updates.notifications.length > 0) {
            this.updateNotifications(updates.notifications);
        }
    }
    
    updateStats(newStats) {
        document.querySelectorAll('.stat-card').forEach(card => {
            const statType = card.dataset.stat;
            if (statType && newStats[statType] !== undefined) {
                const valueElement = card.querySelector('h3');
                if (valueElement) {
                    // Animate number change
                    this.animateValueChange(valueElement, newStats[statType]);
                }
            }
        });
    }
    
    animateValueChange(element, newValue) {
        const oldValue = parseInt(element.textContent.replace(/,/g, ''));
        if (oldValue === newValue) return;
        
        const duration = 1000;
        const start = oldValue;
        const increment = (newValue - oldValue) / (duration / 16);
        let current = oldValue;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= newValue) || (increment < 0 && current <= newValue)) {
                current = newValue;
                clearInterval(timer);
            }
            element.textContent = Math.round(current).toLocaleString();
        }, 16);
    }
    
    updateRecentActivity(activities) {
        const activityList = document.querySelector('.recent-activity .card-list');
        if (!activityList) return;
        
        // Add new activities
        activities.forEach(activity => {
            if (!document.querySelector(`[data-activity-id="${activity.id}"]`)) {
                const activityItem = this.createActivityItem(activity);
                activityList.insertBefore(activityItem, activityList.firstChild);
                
                // Limit to 10 items
                const items = activityList.querySelectorAll('.list-item');
                if (items.length > 10) {
                    items[items.length - 1].remove();
                }
            }
        });
    }
    
    createActivityItem(activity) {
        const item = document.createElement('div');
        item.className = 'list-item';
        item.dataset.activityId = activity.id;
        item.dataset.studentId = activity.student_id;
        item.dataset.storyId = activity.story_id;
        
        const timeAgo = this.getTimeAgo(activity.created_at);
        
        item.innerHTML = `
            <div class="item-info">
                <h4>${activity.student_name}</h4>
                <p class="text-muted">${activity.action}</p>
                <small class="text-muted">${timeAgo}</small>
            </div>
            <span class="badge badge-${activity.type}">${activity.badge_text}</span>
        `;
        
        return item;
    }
    
    getTimeAgo(timestamp) {
        const now = new Date();
        const past = new Date(timestamp);
        const diff = Math.floor((now - past) / 1000); // difference in seconds
        
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
        return `${Math.floor(diff / 604800)}w ago`;
    }
    
    initializeCharts() {
        // Initialize performance chart if canvas exists
        const performanceCanvas = document.getElementById('performance-chart');
        if (performanceCanvas && typeof Chart !== 'undefined') {
            this.createPerformanceChart();
        }
        
        // Initialize class distribution chart
        const classDistributionCanvas = document.getElementById('class-distribution-chart');
        if (classDistributionCanvas && typeof Chart !== 'undefined') {
            this.createClassDistributionChart();
        }
        
        // Initialize activity timeline
        const activityTimelineCanvas = document.getElementById('activity-timeline-chart');
        if (activityTimelineCanvas && typeof Chart !== 'undefined') {
            this.createActivityTimelineChart();
        }
    }
    
    createPerformanceChart() {
        const ctx = document.getElementById('performance-chart').getContext('2d');
        const chartData = JSON.parse(document.getElementById('performance-data')?.textContent || '{}');
        
        if (!chartData.labels || chartData.labels.length === 0) return;
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Average Score (%)',
                    data: chartData.scores,
                    backgroundColor: '#4a6fa5',
                    borderColor: '#3a5a85',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Average Score: ${context.parsed.y}%`;
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
                            text: 'Class'
                        }
                    }
                }
            }
        });
    }
    
    createClassDistributionChart() {
        const ctx = document.getElementById('class-distribution-chart').getContext('2d');
        const chartData = JSON.parse(document.getElementById('class-distribution-data')?.textContent || '{}');
        
        if (!chartData.labels || chartData.labels.length === 0) return;
        
        // Generate colors for each segment
        const backgroundColors = [
            '#4a6fa5', '#6c757d', '#28a745', '#dc3545', '#ffc107',
            '#17a2b8', '#6610f2', '#e83e8c', '#fd7e14', '#20c997'
        ];
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.data,
                    backgroundColor: backgroundColors.slice(0, chartData.labels.length),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} students (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    createActivityTimelineChart() {
        const ctx = document.getElementById('activity-timeline-chart').getContext('2d');
        const chartData = JSON.parse(document.getElementById('activity-timeline-data')?.textContent || '{}');
        
        if (!chartData.labels || chartData.labels.length === 0) return;
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Story Completions',
                    data: chartData.completions,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 2,
                    fill: true
                }, {
                    label: 'Quiz Attempts',
                    data: chartData.quiz_attempts,
                    borderColor: '#4a6fa5',
                    backgroundColor: 'rgba(74, 111, 165, 0.1)',
                    borderWidth: 2,
                    fill: true
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
                            text: 'Count'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }
    
    setupQuickActions() {
        // Setup keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + key shortcuts
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'n':
                        e.preventDefault();
                        window.location.href = '/teacher/story/create';
                        break;
                    case 's':
                        e.preventDefault();
                        window.location.href = '/teacher/students';
                        break;
                    case 'a':
                        e.preventDefault();
                        window.location.href = '/teacher/analytics';
                        break;
                    case 'd':
                        e.preventDefault();
                        window.location.href = '/teacher/dashboard';
                        break;
                }
            }
        });
    }
    
    async loadNotifications() {
        try {
            const response = await fetch('/api/teacher/notifications');
            if (response.ok) {
                const notifications = await response.json();
                this.displayNotifications(notifications);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }
    
    displayNotifications(notifications) {
        const notificationCount = document.getElementById('notification-count');
        const notificationList = document.getElementById('notification-list');
        
        if (!notificationCount || !notificationList) return;
        
        // Update count
        const unreadCount = notifications.filter(n => !n.read).length;
        notificationCount.textContent = unreadCount;
        notificationCount.style.display = unreadCount > 0 ? 'block' : 'none';
        
        // Update list
        notificationList.innerHTML = '';
        
        if (notifications.length === 0) {
            notificationList.innerHTML = '<div class="empty-notifications">No notifications</div>';
            return;
        }
        
        notifications.forEach(notification => {
            const item = this.createNotificationItem(notification);
            notificationList.appendChild(item);
        });
    }
    
    createNotificationItem(notification) {
        const item = document.createElement('div');
        item.className = `notification-item ${notification.read ? 'read' : 'unread'}`;
        item.dataset.notificationId = notification.id;
        
        const timeAgo = this.getTimeAgo(notification.created_at);
        
        item.innerHTML = `
            <div class="notification-icon">
                <i class="fas fa-${this.getNotificationIcon(notification.type)}"></i>
            </div>
            <div class="notification-content">
                <p class="notification-text">${notification.message}</p>
                <small class="notification-time">${timeAgo}</small>
            </div>
            ${!notification.read ? '<div class="notification-dot"></div>' : ''}
        `;
        
        item.addEventListener('click', () => {
            this.handleNotificationClick(notification);
        });
        
        return item;
    }
    
    getNotificationIcon(type) {
        const icons = {
            'student_progress': 'user-graduate',
            'quiz_submitted': 'question-circle',
            'new_student': 'user-plus',
            'story_completed': 'book',
            'warning': 'exclamation-triangle',
            'info': 'info-circle',
            'success': 'check-circle'
        };
        return icons[type] || 'bell';
    }
    
    async handleNotificationClick(notification) {
        // Mark as read
        await this.markNotificationAsRead(notification.id);
        
        // Handle action based on notification type
        switch(notification.type) {
            case 'student_progress':
                window.location.href = `/teacher/students/${notification.data.student_id}`;
                break;
            case 'quiz_submitted':
                window.location.href = `/teacher/story/${notification.data.story_id}`;
                break;
            case 'new_student':
                window.location.href = `/teacher/students?new=${notification.data.student_id}`;
                break;
            default:
                // No action
                break;
        }
    }
    
    async markNotificationAsRead(notificationId) {
        try {
            await fetch(`/api/teacher/notifications/${notificationId}/read`, {
                method: 'POST'
            });
            
            // Update UI
            const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (item) {
                item.classList.remove('unread');
                item.classList.add('read');
                item.querySelector('.notification-dot')?.remove();
                
                // Update count
                const count = document.getElementById('notification-count');
                if (count) {
                    const newCount = parseInt(count.textContent) - 1;
                    if (newCount > 0) {
                        count.textContent = newCount;
                    } else {
                        count.style.display = 'none';
                    }
                }
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async markAllNotificationsAsRead() {
        try {
            await fetch('/api/teacher/notifications/read_all', {
                method: 'POST'
            });
            
            // Update UI
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
                item.classList.add('read');
                item.querySelector('.notification-dot')?.remove();
            });
            
            // Update count
            const count = document.getElementById('notification-count');
            if (count) {
                count.style.display = 'none';
            }
            
            this.showNotification('All notifications marked as read', 'success');
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }
    
    toggleNotificationsPanel() {
        const panel = document.getElementById('notifications-panel');
        if (panel) {
            panel.classList.toggle('show');
        }
    }
    
    handleStatCardAction(action) {
        switch(action) {
            case 'view_stories':
                window.location.href = '/teacher/stories';
                break;
            case 'view_students':
                window.location.href = '/teacher/students';
                break;
            case 'view_analytics':
                window.location.href = '/teacher/analytics';
                break;
            case 'create_story':
                window.location.href = '/teacher/story/create';
                break;
        }
    }
    
    handleQuickAction(actionType) {
        switch(actionType) {
            case 'create-story':
                window.location.href = '/teacher/story/create';
                break;
            case 'manage-students':
                window.location.href = '/teacher/students';
                break;
            case 'view-analytics':
                window.location.href = '/teacher/analytics';
                break;
            case 'export-data':
                this.exportDashboardData();
                break;
        }
    }
    
    async exportDashboardData() {
        try {
            const response = await fetch('/api/teacher/export_dashboard');
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `dashboard_export_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('Dashboard data exported successfully', 'success');
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Error exporting dashboard data:', error);
            this.showNotification('Failed to export data', 'error');
        }
    }
    
    updateStudentProgress(progress) {
        // Update recent activity with new progress
        const activityList = document.querySelector('.recent-activity .card-list');
        if (activityList) {
            const activityItem = this.createActivityItem({
                id: `progress_${Date.now()}`,
                student_name: progress.student_name,
                action: `Completed ${progress.story_title}`,
                type: 'success',
                badge_text: 'Completed',
                created_at: new Date().toISOString(),
                student_id: progress.student_id,
                story_id: progress.story_id
            });
            
            activityList.insertBefore(activityItem, activityList.firstChild);
            
            // Limit to 10 items
            const items = activityList.querySelectorAll('.list-item');
            if (items.length > 10) {
                items[items.length - 1].remove();
            }
        }
        
        // Update stats
        this.incrementStat('total_completions');
    }
    
    handleNewQuizSubmission(quizData) {
        // Show notification
        this.showNotification(
            `${quizData.student_name} submitted a quiz for ${quizData.story_title}`,
            'info'
        );
        
        // Update stats
        this.incrementStat('total_quizzes');
    }
    
    handleNewStudent(studentData) {
        // Show notification
        this.showNotification(
            `New student registered: ${studentData.name} (${studentData.class_level})`,
            'success'
        );
        
        // Update stats
        this.incrementStat('total_students');
    }
    
    incrementStat(statName) {
        const statCard = document.querySelector(`[data-stat="${statName}"]`);
        if (statCard) {
            const valueElement = statCard.querySelector('h3');
            if (valueElement) {
                const currentValue = parseInt(valueElement.textContent.replace(/,/g, ''));
                valueElement.textContent = (currentValue + 1).toLocaleString();
            }
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `teacher-notification alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        // Add to page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(notification, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, 5000);
        }
        
        // Also add to notification panel
        this.addToNotificationPanel(message, type);
    }
    
    addToNotificationPanel(message, type) {
        const notificationList = document.getElementById('notification-list');
        if (!notificationList) return;
        
        const notification = {
            id: `notif_${Date.now()}`,
            message: message,
            type: type,
            read: false,
            created_at: new Date().toISOString()
        };
        
        const item = this.createNotificationItem(notification);
        notificationList.insertBefore(item, notificationList.firstChild);
        
        // Update count
        const count = document.getElementById('notification-count');
        if (count) {
            const currentCount = parseInt(count.textContent) || 0;
            count.textContent = currentCount + 1;
            count.style.display = 'block';
        }
        
        // Limit to 50 notifications
        const items = notificationList.querySelectorAll('.notification-item');
        if (items.length > 50) {
            items[items.length - 1].remove();
        }
    }
}

class StoryManager {
    constructor() {
        this.currentPage = 1;
        this.pages = [];
        this.initializeEventListeners();
        this.setupPageSortable();
        this.setupImageUpload();
        this.setupAutoSave();
        this.loadDraft();
    }
    
    initializeEventListeners() {
        // Add page button
        document.getElementById('add-page')?.addEventListener('click', () => {
            this.addPage();
        });
        
        // Save story button
        document.getElementById('save-story')?.addEventListener('click', () => {
            this.saveStory();
        });
        
        // Publish story button
        document.getElementById('publish-story')?.addEventListener('click', () => {
            this.publishStory();
        });
        
        // Preview story button
        document.getElementById('preview-story')?.addEventListener('click', () => {
            this.previewStory();
        });
        
        // Assign classes toggle
        document.getElementById('assign-to-all')?.addEventListener('change', (e) => {
            this.toggleAssignToAll(e.target.checked);
        });
        
        // Cover image upload
        document.getElementById('cover-image-upload')?.addEventListener('change', (e) => {
            this.handleCoverImageUpload(e);
        });
        
        // Duration change for all pages
        document.getElementById('global-duration')?.addEventListener('change', (e) => {
            this.updateAllPageDurations(e.target.value);
        });
        
        // Bulk actions
        document.getElementById('bulk-actions')?.addEventListener('change', (e) => {
            this.handleBulkAction(e.target.value);
        });
    }
    
    setupPageSortable() {
        const pagesContainer = document.getElementById('pages-container');
        if (!pagesContainer) return;
        
        // Make pages sortable with drag and drop
        new Sortable(pagesContainer, {
            animation: 150,
            handle: '.page-handle',
            onEnd: () => {
                this.renumberPages();
            }
        });
    }
    
    setupImageUpload() {
        // Setup image upload for all page image inputs
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('page-image-upload')) {
                this.handlePageImageUpload(e);
            }
        });
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds
        setInterval(() => {
            this.autoSave();
        }, 30000);
        
        // Save before page unload
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                this.autoSave(true); // Force save
            }
        });
        
        // Save on form changes
        document.querySelectorAll('input, textarea, select').forEach(element => {
            element.addEventListener('change', () => {
                this.markAsChanged();
            });
        });
    }
    
    addPage(afterPage = null) {
        const pageNumber = this.pages.length + 1;
        const pageId = `page_${Date.now()}`;
        
        const pageTemplate = `
            <div class="page-item" data-page-id="${pageId}" data-page-number="${pageNumber}">
                <div class="page-header">
                    <div class="page-handle">
                        <i class="fas fa-grip-vertical"></i>
                    </div>
                    <h3>Page ${pageNumber}</h3>
                    <div class="page-actions">
                        <button type="button" class="btn btn-sm btn-outline move-up" title="Move Up">
                            <i class="fas fa-arrow-up"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline move-down" title="Move Down">
                            <i class="fas fa-arrow-down"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-danger remove-page" title="Remove Page">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <div class="page-content">
                    <div class="form-group">
                        <label>Page Image</label>
                        <div class="image-upload-container">
                            <input type="file" class="page-image-upload" accept="image/*" data-page-id="${pageId}">
                            <div class="image-preview" id="preview-${pageId}">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>Click to upload image</p>
                            </div>
                            <div class="image-actions">
                                <button type="button" class="btn btn-sm btn-outline remove-image" data-page-id="${pageId}">
                                    <i class="fas fa-trash"></i> Remove
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Text Content</label>
                        <textarea class="page-text form-control" rows="4" 
                                  placeholder="Enter the text content for this page..." 
                                  data-page-id="${pageId}"></textarea>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Important Notes</label>
                            <textarea class="page-notes form-control" rows="2" 
                                      placeholder="Add important notes or vocabulary..." 
                                      data-page-id="${pageId}"></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label>Duration (seconds)</label>
                            <input type="number" class="page-duration form-control" value="10" 
                                   min="5" max="60" data-page-id="${pageId}">
                            <small class="form-text">Time to display this page</small>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Narration (Optional)</label>
                        <div class="narration-controls">
                            <button type="button" class="btn btn-sm btn-outline record-narration" data-page-id="${pageId}">
                                <i class="fas fa-microphone"></i> Record
                            </button>
                            <input type="file" class="narration-upload" accept="audio/*" data-page-id="${pageId}">
                            <div class="narration-preview" id="narration-preview-${pageId}">
                                <p>No narration uploaded</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const pagesContainer = document.getElementById('pages-container');
        if (afterPage) {
            const afterElement = document.querySelector(`[data-page-id="${afterPage}"]`);
            if (afterElement) {
                afterElement.insertAdjacentHTML('afterend', pageTemplate);
            } else {
                pagesContainer.insertAdjacentHTML('beforeend', pageTemplate);
            }
        } else {
            pagesContainer.insertAdjacentHTML('beforeend', pageTemplate);
        }
        
        // Add page to array
        this.pages.push({
            id: pageId,
            number: pageNumber,
            image: null,
            text: '',
            notes: '',
            duration: 10,
            narration: null
        });
        
        // Setup event listeners for new page
        this.setupPageEventListeners(pageId);
        
        // Update page count
        this.updatePageCount();
        
        // Mark as changed
        this.markAsChanged();
        
        // Scroll to new page
        setTimeout(() => {
            const newPage = document.querySelector(`[data-page-id="${pageId}"]`);
            if (newPage) {
                newPage.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    }
    
    setupPageEventListeners(pageId) {
        const pageElement = document.querySelector(`[data-page-id="${pageId}"]`);
        if (!pageElement) return;
        
        // Remove page button
        const removeBtn = pageElement.querySelector('.remove-page');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                this.removePage(pageId);
            });
        }
        
        // Move up button
        const moveUpBtn = pageElement.querySelector('.move-up');
        if (moveUpBtn) {
            moveUpBtn.addEventListener('click', () => {
                this.movePageUp(pageId);
            });
        }
        
        // Move down button
        const moveDownBtn = pageElement.querySelector('.move-down');
        if (moveDownBtn) {
            moveDownBtn.addEventListener('click', () => {
                this.movePageDown(pageId);
            });
        }
        
        // Remove image button
        const removeImageBtn = pageElement.querySelector('.remove-image');
        if (removeImageBtn) {
            removeImageBtn.addEventListener('click', () => {
                this.removePageImage(pageId);
            });
        }
        
        // Record narration button
        const recordBtn = pageElement.querySelector('.record-narration');
        if (recordBtn) {
            recordBtn.addEventListener('click', () => {
                this.recordNarration(pageId);
            });
        }
        
        // Text content auto-resize
        const textarea = pageElement.querySelector('.page-text');
        if (textarea) {
            textarea.addEventListener('input', () => {
                this.autoResizeTextarea(textarea);
            });
            this.autoResizeTextarea(textarea); // Initial resize
        }
    }
    
    removePage(pageId) {
        if (this.pages.length <= 1) {
            this.showNotification('Story must have at least one page', 'warning');
            return;
        }
        
        if (confirm('Are you sure you want to remove this page?')) {
            const pageElement = document.querySelector(`[data-page-id="${pageId}"]`);
            if (pageElement) {
                pageElement.remove();
                
                // Remove from array
                this.pages = this.pages.filter(page => page.id !== pageId);
                
                // Renumber pages
                this.renumberPages();
                
                // Mark as changed
                this.markAsChanged();
                
                this.showNotification('Page removed', 'success');
            }
        }
    }
    
    movePageUp(pageId) {
        const pageElement = document.querySelector(`[data-page-id="${pageId}"]`);
        const prevElement = pageElement.previousElementSibling;
        
        if (prevElement && prevElement.classList.contains('page-item')) {
            pageElement.parentNode.insertBefore(pageElement, prevElement);
            this.renumberPages();
            this.markAsChanged();
        }
    }
    
    movePageDown(pageId) {
        const pageElement = document.querySelector(`[data-page-id="${pageId}"]`);
        const nextElement = pageElement.nextElementSibling;
        
        if (nextElement && nextElement.classList.contains('page-item')) {
            pageElement.parentNode.insertBefore(nextElement, pageElement);
            this.renumberPages();
            this.markAsChanged();
        }
    }
    
    renumberPages() {
        const pageItems = document.querySelectorAll('.page-item');
        pageItems.forEach((item, index) => {
            const pageNumber = index + 1;
            item.dataset.pageNumber = pageNumber;
            item.querySelector('h3').textContent = `Page ${pageNumber}`;
            
            // Update in array
            const pageId = item.dataset.pageId;
            const pageIndex = this.pages.findIndex(p => p.id === pageId);
            if (pageIndex !== -1) {
                this.pages[pageIndex].number = pageNumber;
            }
        });
        
        this.updatePageCount();
    }
    
    updatePageCount() {
        const pageCount = this.pages.length;
        document.getElementById('page-count').textContent = `${pageCount} page${pageCount !== 1 ? 's' : ''}`;
    }
    
    async handleCoverImageUpload(event) {
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
            const preview = document.getElementById('cover-image-preview');
            if (preview) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Cover preview">`;
            }
        };
        reader.readAsDataURL(file);
        
        // Upload to server
        const formData = new FormData();
        formData.append('cover_image', file);
        
        try {
            const response = await fetch('/api/teacher/upload_cover_image', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                document.getElementById('cover-image-url').value = data.url;
                this.showNotification('Cover image uploaded successfully', 'success');
                this.markAsChanged();
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            console.error('Error uploading cover image:', error);
            this.showNotification('Failed to upload cover image', 'error');
        }
    }
    
    async handlePageImageUpload(event) {
        const file = event.target.files[0];
        const pageId = event.target.dataset.pageId;
        
        if (!file || !pageId) return;
        
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
            const preview = document.getElementById(`preview-${pageId}`);
            if (preview) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Page image preview">`;
            }
        };
        reader.readAsDataURL(file);
        
        // Update in array
        const pageIndex = this.pages.findIndex(p => p.id === pageId);
        if (pageIndex !== -1) {
            this.pages[pageIndex].image = file;
        }
        
        this.markAsChanged();
    }
    
    removePageImage(pageId) {
        const preview = document.getElementById(`preview-${pageId}`);
        if (preview) {
            preview.innerHTML = `
                <i class="fas fa-cloud-upload-alt"></i>
                <p>Click to upload image</p>
            `;
        }
        
        // Clear file input
        const fileInput = document.querySelector(`[data-page-id="${pageId}"].page-image-upload`);
        if (fileInput) {
            fileInput.value = '';
        }
        
        // Update in array
        const pageIndex = this.pages.findIndex(p => p.id === pageId);
        if (pageIndex !== -1) {
            this.pages[pageIndex].image = null;
        }
        
        this.markAsChanged();
    }
    
    async recordNarration(pageId) {
        // Check if browser supports media recording
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showNotification('Audio recording not supported in this browser', 'error');
            return;
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            const audioChunks = [];
            
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });
            
            mediaRecorder.addEventListener('stop', () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                this.saveNarration(pageId, audioBlob);
            });
            
            // Start recording
            mediaRecorder.start();
            
            // Show recording interface
            this.showRecordingInterface(pageId, mediaRecorder);
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.showNotification('Could not access microphone. Please check permissions.', 'error');
        }
    }
    
    showRecordingInterface(pageId, mediaRecorder) {
        const modal = document.createElement('div');
        modal.className = 'recording-modal';
        modal.innerHTML = `
            <div class="recording-content">
                <h4><i class="fas fa-microphone"></i> Recording Narration</h4>
                <div class="recording-visualizer">
                    <div class="sound-wave"></div>
                </div>
                <div class="recording-timer">00:00</div>
                <div class="recording-controls">
                    <button class="btn btn-danger stop-recording">
                        <i class="fas fa-stop"></i> Stop Recording
                    </button>
                    <button class="btn btn-outline cancel-recording">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Start timer
        let seconds = 0;
        const timerElement = modal.querySelector('.recording-timer');
        const timerInterval = setInterval(() => {
            seconds++;
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }, 1000);
        
        // Stop recording button
        modal.querySelector('.stop-recording').addEventListener('click', () => {
            clearInterval(timerInterval);
            mediaRecorder.stop();
            modal.remove();
            
            // Stop all tracks
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        });
        
        // Cancel button
        modal.querySelector('.cancel-recording').addEventListener('click', () => {
            clearInterval(timerInterval);
            mediaRecorder.stop();
            modal.remove();
            
            // Stop all tracks
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            this.showNotification('Recording cancelled', 'info');
        });
    }
    
    async saveNarration(pageId, audioBlob) {
        const formData = new FormData();
        formData.append('narration', audioBlob, `narration_${pageId}.wav`);
        formData.append('page_id', pageId);
        
        try {
            const response = await fetch('/api/teacher/upload_narration', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update preview
                const preview = document.getElementById(`narration-preview-${pageId}`);
                if (preview) {
                    preview.innerHTML = `
                        <audio controls>
                            <source src="${data.url}" type="audio/wav">
                            Your browser does not support the audio element.
                        </audio>
                    `;
                }
                
                // Update in array
                const pageIndex = this.pages.findIndex(p => p.id === pageId);
                if (pageIndex !== -1) {
                    this.pages[pageIndex].narration = data.url;
                }
                
                this.showNotification('Narration saved successfully', 'success');
                this.markAsChanged();
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            console.error('Error uploading narration:', error);
            this.showNotification('Failed to save narration', 'error');
        }
    }
    
    toggleAssignToAll(checked) {
        const classCheckboxes = document.querySelectorAll('.class-checkbox input');
        classCheckboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
    }
    
    updateAllPageDurations(duration) {
        document.querySelectorAll('.page-duration').forEach(input => {
            input.value = duration;
            
            // Update in array
            const pageId = input.dataset.pageId;
            const pageIndex = this.pages.findIndex(p => p.id === pageId);
            if (pageIndex !== -1) {
                this.pages[pageIndex].duration = parseInt(duration);
            }
        });
        
        this.markAsChanged();
        this.showNotification(`All page durations updated to ${duration} seconds`, 'success');
    }
    
    handleBulkAction(action) {
        switch(action) {
            case 'duplicate_selected':
                this.duplicateSelectedPages();
                break;
            case 'delete_selected':
                this.deleteSelectedPages();
                break;
            case 'clear_text':
                this.clearSelectedText();
                break;
            case 'clear_images':
                this.clearSelectedImages();
                break;
        }
        
        // Reset select
        document.getElementById('bulk-actions').value = '';
    }
    
    duplicateSelectedPages() {
        const selectedPages = this.getSelectedPages();
        if (selectedPages.length === 0) {
            this.showNotification('No pages selected', 'warning');
            return;
        }
        
        selectedPages.forEach(pageId => {
            const pageIndex = this.pages.findIndex(p => p.id === pageId);
            if (pageIndex !== -1) {
                const page = this.pages[pageIndex];
                this.addPage(pageId); // Add after current page
                
                // Copy content to new page
                setTimeout(() => {
                    const newPageId = this.pages[this.pages.length - 1].id;
                    this.copyPageContent(pageId, newPageId);
                }, 100);
            }
        });
        
        this.showNotification(`${selectedPages.length} page(s) duplicated`, 'success');
    }
    
    deleteSelectedPages() {
        const selectedPages = this.getSelectedPages();
        if (selectedPages.length === 0) {
            this.showNotification('No pages selected', 'warning');
            return;
        }
        
        if (confirm(`Are you sure you want to delete ${selectedPages.length} selected page(s)?`)) {
            selectedPages.forEach(pageId => {
                this.removePage(pageId);
            });
        }
    }
    
    clearSelectedText() {
        const selectedPages = this.getSelectedPages();
        if (selectedPages.length === 0) {
            this.showNotification('No pages selected', 'warning');
            return;
        }
        
        selectedPages.forEach(pageId => {
            const textarea = document.querySelector(`[data-page-id="${pageId}"].page-text`);
            if (textarea) {
                textarea.value = '';
                
                // Update in array
                const pageIndex = this.pages.findIndex(p => p.id === pageId);
                if (pageIndex !== -1) {
                    this.pages[pageIndex].text = '';
                }
            }
        });
        
        this.markAsChanged();
        this.showNotification(`Text cleared from ${selectedPages.length} page(s)`, 'success');
    }
    
    clearSelectedImages() {
        const selectedPages = this.getSelectedPages();
        if (selectedPages.length === 0) {
            this.showNotification('No pages selected', 'warning');
            return;
        }
        
        selectedPages.forEach(pageId => {
            this.removePageImage(pageId);
        });
        
        this.showNotification(`Images cleared from ${selectedPages.length} page(s)`, 'success');
    }
    
    getSelectedPages() {
        const selected = [];
        document.querySelectorAll('.page-item').forEach(item => {
            const checkbox = item.querySelector('.page-select input[type="checkbox"]');
            if (checkbox && checkbox.checked) {
                selected.push(item.dataset.pageId);
            }
        });
        return selected;
    }
    
    copyPageContent(sourcePageId, targetPageId) {
        const sourcePage = this.pages.find(p => p.id === sourcePageId);
        const targetPageIndex = this.pages.findIndex(p => p.id === targetPageId);
        
        if (sourcePage && targetPageIndex !== -1) {
            // Copy text
            const targetTextarea = document.querySelector(`[data-page-id="${targetPageId}"].page-text`);
            if (targetTextarea) {
                targetTextarea.value = sourcePage.text;
            }
            
            // Copy notes
            const targetNotes = document.querySelector(`[data-page-id="${targetPageId}"].page-notes`);
            if (targetNotes) {
                targetNotes.value = sourcePage.notes || '';
            }
            
            // Copy duration
            const targetDuration = document.querySelector(`[data-page-id="${targetPageId}"].page-duration`);
            if (targetDuration) {
                targetDuration.value = sourcePage.duration || 10;
            }
            
            // Update in array
            this.pages[targetPageIndex].text = sourcePage.text;
            this.pages[targetPageIndex].notes = sourcePage.notes;
            this.pages[targetPageIndex].duration = sourcePage.duration;
            
            this.markAsChanged();
        }
    }
    
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    
    hasUnsavedChanges() {
        return localStorage.getItem('story_unsaved_changes') === 'true';
    }
    
    markAsChanged() {
        localStorage.setItem('story_unsaved_changes', 'true');
        document.title = document.title.replace(/^\(\*\)\s*/, '') + ' (*)';
    }
    
    markAsSaved() {
        localStorage.removeItem('story_unsaved_changes');
        document.title = document.title.replace(/\s*\(\*\)$/, '');
    }
    
    async autoSave(force = false) {
        if (!this.hasUnsavedChanges() && !force) return;
        
        const storyData = this.collectStoryData();
        
        try {
            const response = await fetch('/api/teacher/auto_save_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(storyData)
            });
            
            if (response.ok) {
                this.markAsSaved();
                this.showNotification('Auto-saved successfully', 'success');
            }
        } catch (error) {
            console.error('Error auto-saving:', error);
        }
    }
    
    async loadDraft() {
        try {
            const response = await fetch('/api/teacher/load_story_draft');
            if (response.ok) {
                const draft = await response.json();
                if (draft && Object.keys(draft).length > 0) {
                    this.loadStoryData(draft);
                    this.showNotification('Draft loaded successfully', 'success');
                }
            }
        } catch (error) {
            console.error('Error loading draft:', error);
        }
    }
    
    collectStoryData() {
        const storyData = {
            title: document.getElementById('story-title')?.value || '',
            description: document.getElementById('story-description')?.value || '',
            cover_image: document.getElementById('cover-image-url')?.value || '',
            is_published: document.getElementById('is-published')?.checked || false,
            assigned_classes: Array.from(document.querySelectorAll('.class-checkbox input:checked'))
                .map(cb => cb.value),
            pages: []
        };
        
        // Collect page data
        document.querySelectorAll('.page-item').forEach(item => {
            const pageId = item.dataset.pageId;
            const pageNumber = parseInt(item.dataset.pageNumber);
            
            const pageData = {
                id: pageId,
                number: pageNumber,
                text: item.querySelector('.page-text')?.value || '',
                notes: item.querySelector('.page-notes')?.value || '',
                duration: parseInt(item.querySelector('.page-duration')?.value || 10)
            };
            
            storyData.pages.push(pageData);
        });
        
        return storyData;
    }
    
    loadStoryData(storyData) {
        // Load basic story info
        if (storyData.title) {
            document.getElementById('story-title').value = storyData.title;
        }
        
        if (storyData.description) {
            document.getElementById('story-description').value = storyData.description;
        }
        
        if (storyData.cover_image) {
            document.getElementById('cover-image-url').value = storyData.cover_image;
            const preview = document.getElementById('cover-image-preview');
            if (preview) {
                preview.innerHTML = `<img src="${storyData.cover_image}" alt="Cover preview">`;
            }
        }
        
        if (storyData.is_published !== undefined) {
            document.getElementById('is-published').checked = storyData.is_published;
        }
        
        // Load assigned classes
        if (storyData.assigned_classes) {
            document.querySelectorAll('.class-checkbox input').forEach(checkbox => {
                checkbox.checked = storyData.assigned_classes.includes(checkbox.value);
            });
        }
        
        // Load pages
        if (storyData.pages && storyData.pages.length > 0) {
            // Clear existing pages
            document.querySelectorAll('.page-item').forEach(item => item.remove());
            this.pages = [];
            
            // Add pages
            storyData.pages.forEach((pageData, index) => {
                this.addPage();
                
                // Set page content after a short delay
                setTimeout(() => {
                    const newPageId = this.pages[this.pages.length - 1].id;
                    this.setPageContent(newPageId, pageData);
                }, 100);
            });
        }
    }
    
    setPageContent(pageId, pageData) {
        const pageElement = document.querySelector(`[data-page-id="${pageId}"]`);
        if (!pageElement) return;
        
        // Set text
        const textarea = pageElement.querySelector('.page-text');
        if (textarea && pageData.text) {
            textarea.value = pageData.text;
            this.autoResizeTextarea(textarea);
        }
        
        // Set notes
        const notes = pageElement.querySelector('.page-notes');
        if (notes && pageData.notes) {
            notes.value = pageData.notes;
        }
        
        // Set duration
        const duration = pageElement.querySelector('.page-duration');
        if (duration && pageData.duration) {
            duration.value = pageData.duration;
        }
        
        // Update in array
        const pageIndex = this.pages.findIndex(p => p.id === pageId);
        if (pageIndex !== -1) {
            this.pages[pageIndex].text = pageData.text || '';
            this.pages[pageIndex].notes = pageData.notes || '';
            this.pages[pageIndex].duration = pageData.duration || 10;
        }
    }
    
    async saveStory() {
        const storyData = this.collectStoryData();
        
        // Validate
        if (!storyData.title.trim()) {
            this.showNotification('Please enter a story title', 'error');
            return;
        }
        
        if (storyData.pages.length === 0) {
            this.showNotification('Please add at least one page', 'error');
            return;
        }
        
        for (const page of storyData.pages) {
            if (!page.text.trim()) {
                this.showNotification(`Page ${page.number} has no text content`, 'error');
                return;
            }
        }
        
        try {
            const response = await fetch('/api/teacher/save_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(storyData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.markAsSaved();
                this.showNotification('Story saved successfully', 'success');
                
                // Update story ID if this is a new story
                if (result.story_id) {
                    window.history.replaceState({}, '', `/teacher/story/${result.story_id}/edit`);
                }
                
                return result.story_id;
            } else {
                throw new Error('Save failed');
            }
        } catch (error) {
            console.error('Error saving story:', error);
            this.showNotification('Failed to save story', 'error');
        }
    }
    
    async publishStory() {
        const storyId = await this.saveStory();
        if (!storyId) return;
        
        try {
            const response = await fetch(`/api/teacher/publish_story/${storyId}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('Story published successfully', 'success');
                
                // Redirect to story management page after 2 seconds
                setTimeout(() => {
                    window.location.href = '/teacher/stories';
                }, 2000);
            } else {
                throw new Error('Publish failed');
            }
        } catch (error) {
            console.error('Error publishing story:', error);
            this.showNotification('Failed to publish story', 'error');
        }
    }
    
    async previewStory() {
        const storyId = await this.saveStory();
        if (!storyId) return;
        
        // Open preview in new tab
        window.open(`/teacher/story/${storyId}/preview`, '_blank');
    }
    
    showNotification(message, type = 'info') {
        // Create notification
        const notification = document.createElement('div');
        notification.className = `story-notification alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        // Add to page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(notification, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, 5000);
        }
    }
}

class QuizManager {
    constructor() {
        this.questions = [];
        this.currentQuestion = 1;
        this.initializeEventListeners();
        this.setupQuestionSortable();
        this.setupQuestionTemplates();
        this.setupAutoSave();
        this.loadDraft();
    }
    
    initializeEventListeners() {
        // Add question button
        document.getElementById('add-question')?.addEventListener('click', () => {
            this.addQuestion();
        });
        
        // Save quiz button
        document.getElementById('save-quiz')?.addEventListener('click', () => {
            this.saveQuiz();
        });
        
        // Preview quiz button
        document.getElementById('preview-quiz')?.addEventListener('click', () => {
            this.previewQuiz();
        });
        
        // Question type change
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('question-type')) {
                this.handleQuestionTypeChange(e);
            }
        });
        
        // Correct answer change
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('correct-answer')) {
                this.handleCorrectAnswerChange(e);
            }
        });
        
        // Bulk actions
        document.getElementById('quiz-bulk-actions')?.addEventListener('change', (e) => {
            this.handleQuizBulkAction(e.target.value);
        });
        
        // Timer preset buttons
        document.querySelectorAll('.timer-preset').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const minutes = parseInt(button.dataset.minutes);
                document.getElementById('time-limit').value = minutes * 60;
            });
        });
        
        // Passing score preset buttons
        document.querySelectorAll('.score-preset').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const score = parseInt(button.dataset.score);
                document.getElementById('passing-score').value = score;
            });
        });
    }
    
    setupQuestionSortable() {
        const questionsContainer = document.getElementById('questions-container');
        if (!questionsContainer) return;
        
        // Make questions sortable with drag and drop
        new Sortable(questionsContainer, {
            animation: 150,
            handle: '.question-handle',
            onEnd: () => {
                this.renumberQuestions();
            }
        });
    }
    
    setupQuestionTemplates() {
        // Store question templates
        this.questionTemplates = {
            multiple_choice: `
                <div class="form-group">
                    <label>Option A *</label>
                    <input type="text" class="option-a form-control" required>
                </div>
                <div class="form-group">
                    <label>Option B *</label>
                    <input type="text" class="option-b form-control" required>
                </div>
                <div class="form-group">
                    <label>Option C</label>
                    <input type="text" class="option-c form-control">
                </div>
                <div class="form-group">
                    <label>Option D</label>
                    <input type="text" class="option-d form-control">
                </div>
                <div class="form-group">
                    <label>Correct Answer *</label>
                    <select class="correct-answer form-control" required>
                        <option value="">Select correct answer</option>
                        <option value="A">Option A</option>
                        <option value="B">Option B</option>
                        <option value="C">Option C</option>
                        <option value="D">Option D</option>
                    </select>
                </div>
            `,
            
            true_false: `
                <div class="form-group">
                    <label>Correct Answer *</label>
                    <select class="correct-answer form-control" required>
                        <option value="">Select correct answer</option>
                        <option value="True">True</option>
                        <option value="False">False</option>
                    </select>
                </div>
            `,
            
            short_answer: `
                <div class="form-group">
                    <label>Correct Answer *</label>
                    <input type="text" class="correct-answer form-control" required 
                           placeholder="Enter the correct answer">
                    <small class="form-text">For short answer questions, consider multiple correct variations</small>
                </div>
            `
        };
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds
        setInterval(() => {
            this.autoSave();
        }, 30000);
        
        // Save before page unload
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                this.autoSave(true); // Force save
            }
        });
        
        // Save on form changes
        document.querySelectorAll('input, textarea, select').forEach(element => {
            element.addEventListener('change', () => {
                this.markAsChanged();
            });
        });
    }
    
    addQuestion(afterQuestion = null) {
        const questionNumber = this.questions.length + 1;
        const questionId = `question_${Date.now()}`;
        
        const questionTemplate = `
            <div class="question-item" data-question-id="${questionId}" data-question-number="${questionNumber}">
                <div class="question-header">
                    <div class="question-handle">
                        <i class="fas fa-grip-vertical"></i>
                    </div>
                    <h3>Question ${questionNumber}</h3>
                    <div class="question-actions">
                        <button type="button" class="btn btn-sm btn-outline move-up" title="Move Up">
                            <i class="fas fa-arrow-up"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline move-down" title="Move Down">
                            <i class="fas fa-arrow-down"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-danger remove-question" title="Remove Question">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <div class="question-content">
                    <div class="form-group">
                        <label>Question Text *</label>
                        <textarea class="question-text form-control" rows="3" 
                                  placeholder="Enter your question..." 
                                  data-question-id="${questionId}" required></textarea>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Question Type *</label>
                            <select class="question-type form-control" data-question-id="${questionId}" required>
                                <option value="">Select type</option>
                                <option value="multiple_choice">Multiple Choice</option>
                                <option value="true_false">True/False</option>
                                <option value="short_answer">Short Answer</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label>Points</label>
                            <input type="number" class="question-points form-control" value="1" 
                                   min="1" max="10" data-question-id="${questionId}">
                        </div>
                    </div>
                    
                    <div class="question-options" id="options-${questionId}">
                        <!-- Options will be loaded based on question type -->
                    </div>
                    
                    <div class="form-group">
                        <label>Explanation (Optional)</label>
                        <textarea class="explanation form-control" rows="2" 
                                  placeholder="Add explanation for the correct answer..." 
                                  data-question-id="${questionId}"></textarea>
                    </div>
                </div>
            </div>
        `;
        
        const questionsContainer = document.getElementById('questions-container');
        if (afterQuestion) {
            const afterElement = document.querySelector(`[data-question-id="${afterQuestion}"]`);
            if (afterElement) {
                afterElement.insertAdjacentHTML('afterend', questionTemplate);
            } else {
                questionsContainer.insertAdjacentHTML('beforeend', questionTemplate);
            }
        } else {
            questionsContainer.insertAdjacentHTML('beforeend', questionTemplate);
        }
        
        // Add question to array
        this.questions.push({
            id: questionId,
            number: questionNumber,
            text: '',
            type: '',
            points: 1,
            options: {},
            correct_answer: '',
            explanation: ''
        });
        
        // Setup event listeners for new question
        this.setupQuestionEventListeners(questionId);
        
        // Update question count
        this.updateQuestionCount();
        
        // Mark as changed
        this.markAsChanged();
        
        // Scroll to new question
        setTimeout(() => {
            const newQuestion = document.querySelector(`[data-question-id="${questionId}"]`);
            if (newQuestion) {
                newQuestion.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    }
    
    setupQuestionEventListeners(questionId) {
        const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
        if (!questionElement) return;
        
        // Remove question button
        const removeBtn = questionElement.querySelector('.remove-question');
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                this.removeQuestion(questionId);
            });
        }
        
        // Move up button
        const moveUpBtn = questionElement.querySelector('.move-up');
        if (moveUpBtn) {
            moveUpBtn.addEventListener('click', () => {
                this.moveQuestionUp(questionId);
            });
        }
        
        // Move down button
        const moveDownBtn = questionElement.querySelector('.move-down');
        if (moveDownBtn) {
            moveDownBtn.addEventListener('click', () => {
                this.moveQuestionDown(questionId);
            });
        }
        
        // Question type change
        const typeSelect = questionElement.querySelector('.question-type');
        if (typeSelect) {
            typeSelect.addEventListener('change', (e) => {
                this.handleQuestionTypeChange(e);
            });
        }
        
        // Auto-resize textarea
        const textarea = questionElement.querySelector('.question-text');
        if (textarea) {
            textarea.addEventListener('input', () => {
                this.autoResizeTextarea(textarea);
            });
            this.autoResizeTextarea(textarea); // Initial resize
        }
    }
    
    handleQuestionTypeChange(event) {
        const questionId = event.target.dataset.questionId;
        const questionType = event.target.value;
        
        const optionsContainer = document.getElementById(`options-${questionId}`);
        if (!optionsContainer) return;
        
        // Clear existing options
        optionsContainer.innerHTML = '';
        
        // Load new options based on type
        if (this.questionTemplates[questionType]) {
            optionsContainer.innerHTML = this.questionTemplates[questionType];
            
            // Update in array
            const questionIndex = this.questions.findIndex(q => q.id === questionId);
            if (questionIndex !== -1) {
                this.questions[questionIndex].type = questionType;
                this.questions[questionIndex].options = {};
                this.questions[questionIndex].correct_answer = '';
            }
            
            // Setup event listeners for new inputs
            this.setupOptionEventListeners(questionId);
            
            // Mark as changed
            this.markAsChanged();
        }
    }
    
    setupOptionEventListeners(questionId) {
        const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
        if (!questionElement) return;
        
        // Setup input listeners for options
        questionElement.querySelectorAll('.option-a, .option-b, .option-c, .option-d').forEach(input => {
            input.addEventListener('input', () => {
                this.updateQuestionOptions(questionId);
            });
        });
        
        // Setup listener for correct answer select
        const correctAnswerSelect = questionElement.querySelector('.correct-answer');
        if (correctAnswerSelect) {
            correctAnswerSelect.addEventListener('change', () => {
                this.updateCorrectAnswer(questionId, correctAnswerSelect.value);
            });
        }
    }
    
    updateQuestionOptions(questionId) {
        const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
        if (!questionElement) return;
        
        const questionIndex = this.questions.findIndex(q => q.id === questionId);
        if (questionIndex === -1) return;
        
        // Collect options
        const options = {};
        ['a', 'b', 'c', 'd'].forEach(letter => {
            const input = questionElement.querySelector(`.option-${letter}`);
            if (input && input.value.trim()) {
                options[letter.toUpperCase()] = input.value.trim();
            }
        });
        
        // Update in array
        this.questions[questionIndex].options = options;
        
        // Update correct answer options if it's a multiple choice question
        const correctAnswerSelect = questionElement.querySelector('.correct-answer');
        if (correctAnswerSelect && this.questions[questionIndex].type === 'multiple_choice') {
            // Store current value
            const currentValue = correctAnswerSelect.value;
            
            // Update options
            correctAnswerSelect.innerHTML = `
                <option value="">Select correct answer</option>
                ${Object.keys(options).map(letter => 
                    `<option value="${letter}" ${currentValue === letter ? 'selected' : ''}>Option ${letter}</option>`
                ).join('')}
            `;
        }
        
        this.markAsChanged();
    }
    
    updateCorrectAnswer(questionId, answer) {
        const questionIndex = this.questions.findIndex(q => q.id === questionId);
        if (questionIndex !== -1) {
            this.questions[questionIndex].correct_answer = answer;
            this.markAsChanged();
        }
    }
    
    handleCorrectAnswerChange(event) {
        const questionElement = event.target.closest('.question-item');
        if (!questionElement) return;
        
        const questionId = questionElement.dataset.questionId;
        const answer = event.target.value;
        
        this.updateCorrectAnswer(questionId, answer);
    }
    
    removeQuestion(questionId) {
        if (this.questions.length <= 1) {
            this.showNotification('Quiz must have at least one question', 'warning');
            return;
        }
        
        if (confirm('Are you sure you want to remove this question?')) {
            const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
            if (questionElement) {
                questionElement.remove();
                
                // Remove from array
                this.questions = this.questions.filter(q => q.id !== questionId);
                
                // Renumber questions
                this.renumberQuestions();
                
                // Mark as changed
                this.markAsChanged();
                
                this.showNotification('Question removed', 'success');
            }
        }
    }
    
    moveQuestionUp(questionId) {
        const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
        const prevElement = questionElement.previousElementSibling;
        
        if (prevElement && prevElement.classList.contains('question-item')) {
            questionElement.parentNode.insertBefore(questionElement, prevElement);
            this.renumberQuestions();
            this.markAsChanged();
        }
    }
    
    moveQuestionDown(questionId) {
        const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
        const nextElement = questionElement.nextElementSibling;
        
        if (nextElement && nextElement.classList.contains('question-item')) {
            questionElement.parentNode.insertBefore(nextElement, questionElement);
            this.renumberQuestions();
            this.markAsChanged();
        }
    }
    
    renumberQuestions() {
        const questionItems = document.querySelectorAll('.question-item');
        questionItems.forEach((item, index) => {
            const questionNumber = index + 1;
            item.dataset.questionNumber = questionNumber;
            item.querySelector('h3').textContent = `Question ${questionNumber}`;
            
            // Update in array
            const questionId = item.dataset.questionId;
            const questionIndex = this.questions.findIndex(q => q.id === questionId);
            if (questionIndex !== -1) {
                this.questions[questionIndex].number = questionNumber;
            }
        });
        
        this.updateQuestionCount();
    }
    
    updateQuestionCount() {
        const questionCount = this.questions.length;
        document.getElementById('question-count').textContent = `${questionCount} question${questionCount !== 1 ? 's' : ''}`;
        
        // Update total points
        const totalPoints = this.questions.reduce((sum, q) => sum + (q.points || 1), 0);
        document.getElementById('total-points').textContent = `${totalPoints} point${totalPoints !== 1 ? 's' : ''}`;
    }
    
    handleQuizBulkAction(action) {
        switch(action) {
            case 'duplicate_selected_questions':
                this.duplicateSelectedQuestions();
                break;
            case 'delete_selected_questions':
                this.deleteSelectedQuestions();
                break;
            case 'set_points_all':
                this.setPointsForAll();
                break;
            case 'randomize_order':
                this.randomizeQuestionOrder();
                break;
        }
        
        // Reset select
        document.getElementById('quiz-bulk-actions').value = '';
    }
    
    duplicateSelectedQuestions() {
        const selectedQuestions = this.getSelectedQuestions();
        if (selectedQuestions.length === 0) {
            this.showNotification('No questions selected', 'warning');
            return;
        }
        
        selectedQuestions.forEach(questionId => {
            const questionIndex = this.questions.findIndex(q => q.id === questionId);
            if (questionIndex !== -1) {
                const question = this.questions[questionIndex];
                this.addQuestion(questionId); // Add after current question
                
                // Copy content to new question
                setTimeout(() => {
                    const newQuestionId = this.questions[this.questions.length - 1].id;
                    this.copyQuestionContent(questionId, newQuestionId);
                }, 100);
            }
        });
        
        this.showNotification(`${selectedQuestions.length} question(s) duplicated`, 'success');
    }
    
    deleteSelectedQuestions() {
        const selectedQuestions = this.getSelectedQuestions();
        if (selectedQuestions.length === 0) {
            this.showNotification('No questions selected', 'warning');
            return;
        }
        
        if (confirm(`Are you sure you want to delete ${selectedQuestions.length} selected question(s)?`)) {
            selectedQuestions.forEach(questionId => {
                this.removeQuestion(questionId);
            });
        }
    }
    
    setPointsForAll() {
        const points = prompt('Enter points for all questions:', '1');
        if (points && !isNaN(points) && points > 0) {
            const pointValue = parseInt(points);
            
            this.questions.forEach((question, index) => {
                question.points = pointValue;
                
                // Update UI
                const questionElement = document.querySelector(`[data-question-id="${question.id}"]`);
                if (questionElement) {
                    const pointsInput = questionElement.querySelector('.question-points');
                    if (pointsInput) {
                        pointsInput.value = pointValue;
                    }
                }
            });
            
            this.updateQuestionCount();
            this.markAsChanged();
            this.showNotification(`All questions set to ${pointValue} point(s)`, 'success');
        }
    }
    
    randomizeQuestionOrder() {
        if (this.questions.length < 2) {
            this.showNotification('Need at least 2 questions to randomize', 'warning');
            return;
        }
        
        // Shuffle array using Fisher-Yates algorithm
        for (let i = this.questions.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.questions[i], this.questions[j]] = [this.questions[j], this.questions[i]];
        }
        
        // Re-render questions
        this.renderQuestions();
        
        this.markAsChanged();
        this.showNotification('Question order randomized', 'success');
    }
    
    getSelectedQuestions() {
        const selected = [];
        document.querySelectorAll('.question-item').forEach(item => {
            const checkbox = item.querySelector('.question-select input[type="checkbox"]');
            if (checkbox && checkbox.checked) {
                selected.push(item.dataset.questionId);
            }
        });
        return selected;
    }
    
    copyQuestionContent(sourceQuestionId, targetQuestionId) {
        const sourceQuestion = this.questions.find(q => q.id === sourceQuestionId);
        const targetQuestionIndex = this.questions.findIndex(q => q.id === targetQuestionId);
        
        if (sourceQuestion && targetQuestionIndex !== -1) {
            // Copy basic info
            this.questions[targetQuestionIndex].text = sourceQuestion.text;
            this.questions[targetQuestionIndex].type = sourceQuestion.type;
            this.questions[targetQuestionIndex].points = sourceQuestion.points;
            this.questions[targetQuestionIndex].options = { ...sourceQuestion.options };
            this.questions[targetQuestionIndex].correct_answer = sourceQuestion.correct_answer;
            this.questions[targetQuestionIndex].explanation = sourceQuestion.explanation;
            
            // Update UI
            const targetElement = document.querySelector(`[data-question-id="${targetQuestionId}"]`);
            if (targetElement) {
                // Set text
                const textarea = targetElement.querySelector('.question-text');
                if (textarea) {
                    textarea.value = sourceQuestion.text;
                    this.autoResizeTextarea(textarea);
                }
                
                // Set type
                const typeSelect = targetElement.querySelector('.question-type');
                if (typeSelect) {
                    typeSelect.value = sourceQuestion.type;
                    this.handleQuestionTypeChange({ target: typeSelect });
                }
                
                // Set points
                const pointsInput = targetElement.querySelector('.question-points');
                if (pointsInput) {
                    pointsInput.value = sourceQuestion.points;
                }
                
                // Set options (after a delay to allow options to render)
                setTimeout(() => {
                    ['a', 'b', 'c', 'd'].forEach(letter => {
                        const optionValue = sourceQuestion.options[letter.toUpperCase()];
                        if (optionValue) {
                            const optionInput = targetElement.querySelector(`.option-${letter}`);
                            if (optionInput) {
                                optionInput.value = optionValue;
                            }
                        }
                    });
                    
                    // Set correct answer
                    const correctAnswerInput = targetElement.querySelector('.correct-answer');
                    if (correctAnswerInput) {
                        if (correctAnswerInput.tagName === 'SELECT') {
                            correctAnswerInput.value = sourceQuestion.correct_answer;
                        } else {
                            correctAnswerInput.value = sourceQuestion.correct_answer;
                        }
                    }
                    
                    // Set explanation
                    const explanationTextarea = targetElement.querySelector('.explanation');
                    if (explanationTextarea && sourceQuestion.explanation) {
                        explanationTextarea.value = sourceQuestion.explanation;
                    }
                }, 100);
            }
            
            this.markAsChanged();
        }
    }
    
    renderQuestions() {
        const questionsContainer = document.getElementById('questions-container');
        if (!questionsContainer) return;
        
        // Clear container
        questionsContainer.innerHTML = '';
        
        // Re-add all questions in new order
        this.questions.forEach((question, index) => {
            this.addQuestion();
            
            // Set question content after a short delay
            setTimeout(() => {
                const newQuestionId = this.questions[this.questions.length - 1].id;
                this.setQuestionContent(newQuestionId, question);
            }, 100 * (index + 1));
        });
        
        // Remove the extra questions added by addQuestion()
        const currentCount = document.querySelectorAll('.question-item').length;
        const extraCount = currentCount - this.questions.length;
        for (let i = 0; i < extraCount; i++) {
            const lastQuestion = document.querySelector('.question-item:last-child');
            if (lastQuestion) {
                lastQuestion.remove();
            }
        }
    }
    
    setQuestionContent(questionId, questionData) {
        const questionElement = document.querySelector(`[data-question-id="${questionId}"]`);
        if (!questionElement) return;
        
        // Set text
        const textarea = questionElement.querySelector('.question-text');
        if (textarea && questionData.text) {
            textarea.value = questionData.text;
            this.autoResizeTextarea(textarea);
        }
        
        // Set type
        const typeSelect = questionElement.querySelector('.question-type');
        if (typeSelect && questionData.type) {
            typeSelect.value = questionData.type;
            
            // Trigger change event to load options
            const event = new Event('change');
            typeSelect.dispatchEvent(event);
        }
        
        // Set points
        const pointsInput = questionElement.querySelector('.question-points');
        if (pointsInput && questionData.points) {
            pointsInput.value = questionData.points;
        }
        
        // Set explanation
        const explanationTextarea = questionElement.querySelector('.explanation');
        if (explanationTextarea && questionData.explanation) {
            explanationTextarea.value = questionData.explanation;
        }
        
        // Set options and correct answer (after a delay to allow options to render)
        setTimeout(() => {
            if (questionData.type === 'multiple_choice') {
                // Set options
                Object.keys(questionData.options || {}).forEach(letter => {
                    const optionInput = questionElement.querySelector(`.option-${letter.toLowerCase()}`);
                    if (optionInput && questionData.options[letter]) {
                        optionInput.value = questionData.options[letter];
                    }
                });
                
                // Set correct answer
                const correctAnswerSelect = questionElement.querySelector('.correct-answer');
                if (correctAnswerSelect && questionData.correct_answer) {
                    correctAnswerSelect.value = questionData.correct_answer;
                }
            } else if (questionData.type === 'true_false' || questionData.type === 'short_answer') {
                const correctAnswerInput = questionElement.querySelector('.correct-answer');
                if (correctAnswerInput && questionData.correct_answer) {
                    correctAnswerInput.value = questionData.correct_answer;
                }
            }
        }, 200);
    }
    
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    
    hasUnsavedChanges() {
        return localStorage.getItem('quiz_unsaved_changes') === 'true';
    }
    
    markAsChanged() {
        localStorage.setItem('quiz_unsaved_changes', 'true');
        document.title = document.title.replace(/^\(\*\)\s*/, '') + ' (*)';
    }
    
    markAsSaved() {
        localStorage.removeItem('quiz_unsaved_changes');
        document.title = document.title.replace(/\s*\(\*\)$/, '');
    }
    
    async autoSave(force = false) {
        if (!this.hasUnsavedChanges() && !force) return;
        
        const quizData = this.collectQuizData();
        
        try {
            const response = await fetch('/api/teacher/auto_save_quiz', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(quizData)
            });
            
            if (response.ok) {
                this.markAsSaved();
                this.showNotification('Auto-saved successfully', 'success');
            }
        } catch (error) {
            console.error('Error auto-saving:', error);
        }
    }
    
    async loadDraft() {
        try {
            const response = await fetch('/api/teacher/load_quiz_draft');
            if (response.ok) {
                const draft = await response.json();
                if (draft && Object.keys(draft).length > 0) {
                    this.loadQuizData(draft);
                    this.showNotification('Draft loaded successfully', 'success');
                }
            }
        } catch (error) {
            console.error('Error loading draft:', error);
        }
    }
    
    collectQuizData() {
        const quizData = {
            title: document.getElementById('quiz-title')?.value || '',
            description: document.getElementById('quiz-description')?.value || '',
            time_limit: parseInt(document.getElementById('time-limit')?.value || 600),
            passing_score: parseInt(document.getElementById('passing-score')?.value || 60),
            questions: []
        };
        
        // Collect question data
        this.questions.forEach(question => {
            const questionElement = document.querySelector(`[data-question-id="${question.id}"]`);
            if (!questionElement) return;
            
            const questionData = {
                id: question.id,
                number: question.number,
                text: questionElement.querySelector('.question-text')?.value || '',
                type: questionElement.querySelector('.question-type')?.value || '',
                points: parseInt(questionElement.querySelector('.question-points')?.value || 1),
                options: {},
                correct_answer: '',
                explanation: questionElement.querySelector('.explanation')?.value || ''
            };
            
            // Get options based on type
            if (questionData.type === 'multiple_choice') {
                ['a', 'b', 'c', 'd'].forEach(letter => {
                    const input = questionElement.querySelector(`.option-${letter}`);
                    if (input && input.value.trim()) {
                        questionData.options[letter.toUpperCase()] = input.value.trim();
                    }
                });
                
                const correctAnswerSelect = questionElement.querySelector('.correct-answer');
                if (correctAnswerSelect) {
                    questionData.correct_answer = correctAnswerSelect.value;
                }
            } else if (questionData.type === 'true_false') {
                const correctAnswerSelect = questionElement.querySelector('.correct-answer');
                if (correctAnswerSelect) {
                    questionData.correct_answer = correctAnswerSelect.value;
                }
            } else if (questionData.type === 'short_answer') {
                const correctAnswerInput = questionElement.querySelector('.correct-answer');
                if (correctAnswerInput) {
                    questionData.correct_answer = correctAnswerInput.value.trim();
                }
            }
            
            quizData.questions.push(questionData);
        });
        
        return quizData;
    }
    
    loadQuizData(quizData) {
        // Load basic quiz info
        if (quizData.title) {
            document.getElementById('quiz-title').value = quizData.title;
        }
        
        if (quizData.description) {
            document.getElementById('quiz-description').value = quizData.description;
        }
        
        if (quizData.time_limit) {
            document.getElementById('time-limit').value = quizData.time_limit;
        }
        
        if (quizData.passing_score) {
            document.getElementById('passing-score').value = quizData.passing_score;
        }
        
        // Load questions
        if (quizData.questions && quizData.questions.length > 0) {
            // Clear existing questions
            document.querySelectorAll('.question-item').forEach(item => item.remove());
            this.questions = [];
            
            // Add questions
            quizData.questions.forEach((questionData, index) => {
                this.addQuestion();
                
                // Set question content after a short delay
                setTimeout(() => {
                    const newQuestionId = this.questions[this.questions.length - 1].id;
                    this.setQuestionContent(newQuestionId, questionData);
                }, 100 * (index + 1));
            });
            
            // Remove the extra question added by the last addQuestion()
            setTimeout(() => {
                const questionCount = document.querySelectorAll('.question-item').length;
                if (questionCount > quizData.questions.length) {
                    const lastQuestion = document.querySelector('.question-item:last-child');
                    if (lastQuestion) {
                        lastQuestion.remove();
                        this.questions.pop();
                    }
                }
            }, 100 * (quizData.questions.length + 1));
        }
    }
    
    async saveQuiz() {
        const quizData = this.collectQuizData();
        
        // Validate
        if (!quizData.title.trim()) {
            this.showNotification('Please enter a quiz title', 'error');
            return;
        }
        
        if (quizData.questions.length === 0) {
            this.showNotification('Please add at least one question', 'error');
            return;
        }
        
        for (const question of quizData.questions) {
            if (!question.text.trim()) {
                this.showNotification(`Question ${question.number} has no text`, 'error');
                return;
            }
            
            if (!question.type) {
                this.showNotification(`Question ${question.number} has no type selected`, 'error');
                return;
            }
            
            if (!question.correct_answer) {
                this.showNotification(`Question ${question.number} has no correct answer`, 'error');
                return;
            }
            
            if (question.type === 'multiple_choice') {
                const hasOptions = Object.keys(question.options).length >= 2;
                if (!hasOptions) {
                    this.showNotification(`Question ${question.number} needs at least 2 options`, 'error');
                    return;
                }
            }
        }
        
        try {
            const response = await fetch('/api/teacher/save_quiz', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(quizData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.markAsSaved();
                this.showNotification('Quiz saved successfully', 'success');
                
                // Update quiz ID if this is a new quiz
                if (result.quiz_id) {
                    window.history.replaceState({}, '', `/teacher/quiz/${result.quiz_id}/edit`);
                }
                
                return result.quiz_id;
            } else {
                throw new Error('Save failed');
            }
        } catch (error) {
            console.error('Error saving quiz:', error);
            this.showNotification('Failed to save quiz', 'error');
        }
    }
    
    async previewQuiz() {
        const quizId = await this.saveQuiz();
        if (!quizId) return;
        
        // Open preview in new tab
        window.open(`/teacher/quiz/${quizId}/preview`, '_blank');
    }
    
    showNotification(message, type = 'info') {
        // Create notification
        const notification = document.createElement('div');
        notification.className = `quiz-notification alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        // Add to page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(notification, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, 5000);
        }
    }
}

// Initialize based on current page
document.addEventListener('DOMContentLoaded', function() {
    const path = window.location.pathname;
    
    if (path.includes('/teacher/dashboard')) {
        window.teacherDashboard = new TeacherDashboard();
    } 
    else if (path.includes('/teacher/story/create') || path.includes('/teacher/story/') && path.includes('/edit')) {
        window.storyManager = new StoryManager();
    }
    else if (path.includes('/teacher/quiz/create') || (path.includes('/teacher/story/') && path.includes('/quiz'))) {
        window.quizManager = new QuizManager();
    }
    
    // Add global teacher functions
    window.teacherFunctions = {
        exportData: function(type) {
            let endpoint = '';
            let filename = '';
            
            switch(type) {
                case 'students':
                    endpoint = '/api/teacher/export_students';
                    filename = `students_export_${new Date().toISOString().split('T')[0]}.csv`;
                    break;
                case 'stories':
                    endpoint = '/api/teacher/export_stories';
                    filename = `stories_export_${new Date().toISOString().split('T')[0]}.json`;
                    break;
                case 'analytics':
                    endpoint = '/api/teacher/export_analytics';
                    filename = `analytics_export_${new Date().toISOString().split('T')[0]}.pdf`;
                    break;
                default:
                    return;
            }
            
            fetch(endpoint)
                .then(response => response.blob())
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                })
                .catch(error => {
                    console.error('Error exporting data:', error);
                    this.showNotification('Failed to export data', 'error');
                });
        },
        
        bulkAction: function(action, ids) {
            if (!ids || ids.length === 0) {
                this.showNotification('No items selected', 'warning');
                return;
            }
            
            let endpoint = '';
            let data = { ids: ids };
            
            switch(action) {
                case 'publish_stories':
                    endpoint = '/api/teacher/bulk_publish_stories';
                    break;
                case 'archive_stories':
                    endpoint = '/api/teacher/bulk_archive_stories';
                    break;
                case 'delete_stories':
                    if (!confirm(`Are you sure you want to delete ${ids.length} story(s)?`)) return;
                    endpoint = '/api/teacher/bulk_delete_stories';
                    break;
                case 'assign_stories':
                    const classLevel = prompt('Enter class level to assign stories to:');
                    if (!classLevel) return;
                    data.class_level = classLevel;
                    endpoint = '/api/teacher/bulk_assign_stories';
                    break;
                default:
                    return;
            }
            
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    this.showNotification(result.message || 'Action completed successfully', 'success');
                    // Reload page after 2 seconds
                    setTimeout(() => location.reload(), 2000);
                } else {
                    throw new Error(result.message || 'Action failed');
                }
            })
            .catch(error => {
                console.error('Error performing bulk action:', error);
                this.showNotification(error.message || 'Failed to perform action', 'error');
            });
        },
        
        showNotification: function(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `global-teacher-notification alert alert-${type} alert-dismissible fade show`;
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                ${message}
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, 5000);
        }
    };
});