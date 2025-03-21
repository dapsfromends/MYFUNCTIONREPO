// TaskHub Application JavaScript
// Connects to the Azure Functions API

// Configuration
const API_BASE_URL = 'https://polite-water-087e71b10.6.azurestaticapps.net'; 

// DOM Elements
const taskForm = document.getElementById('task-form');
const tasksContainer = document.getElementById('tasks-container');
const statusFilter = document.getElementById('status-filter');
const titleInput = document.getElementById('title');
const descriptionInput = document.getElementById('description');

// Analytics Elements
const totalTasksElement = document.getElementById('total-tasks');
const completedTasksElement = document.getElementById('completed-tasks');
const pendingTasksElement = document.getElementById('pending-tasks');
const completionPercentageElement = document.getElementById('completion-percentage');

// Event Listeners
document.addEventListener('DOMContentLoaded', initialize);
taskForm.addEventListener('submit', createTask);
statusFilter.addEventListener('change', loadTasks);

// Initialization Function
function initialize() {
    loadTasks();
    loadAnalytics();
}

// API Functions
async function loadTasks() {
    tasksContainer.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i> Loading tasks...
        </div>
    `;
    
    const status = statusFilter.value;
    let url = `${API_BASE_URL}/tasks`;
    
    if (status !== 'all') {
        url += `?status=${status}`;
    }
    
    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Server responded with an error');
        }
        
        const tasks = await response.json();
        renderTasks(tasks);
    } catch (error) {
        console.error('Error loading tasks:', error);
        tasksContainer.innerHTML = `
            <div class="empty-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Failed to load tasks. Please try again later.</p>
            </div>
        `;
    }
}

function renderTasks(tasks) {
    if (tasks.length === 0) {
        tasksContainer.innerHTML = `
            <div class="empty-message">
                <i class="fas fa-clipboard"></i>
                <p>No tasks found. Create your first task to get started!</p>
            </div>
        `;
        return;
    }
    
    tasksContainer.innerHTML = '';
    
    tasks.forEach(task => {
        const createdDate = new Date(task.created_at);
        const formattedDate = createdDate.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        const statusClass = task.status === 'completed' ? 'completed' : 'pending';
        
        const taskElement = document.createElement('div');
        taskElement.className = 'task-item';
        
        taskElement.innerHTML = `
            <h3>${escapeHtml(task.title)}</h3>
            <p>${escapeHtml(task.description || 'No description')}</p>
            <div class="task-meta">
                <span class="task-date">
                    <i class="far fa-calendar-alt"></i> ${formattedDate}
                </span>
                <span class="status ${statusClass}">
                    ${task.status}
                </span>
            </div>
            <div class="task-actions">
                ${task.status !== 'completed' ? 
                    `<button class="btn success-btn complete-btn" data-id="${task.id}">
                        <i class="fas fa-check"></i> Mark Complete
                    </button>` : ''}
                <button class="btn danger-btn delete-btn" data-id="${task.id}">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        `;
        
        tasksContainer.appendChild(taskElement);
    });
    
    // Add event listeners to buttons
    document.querySelectorAll('.complete-btn').forEach(button => {
        button.addEventListener('click', completeTask);
    });
    
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', deleteTask);
    });
}

async function createTask(e) {
    e.preventDefault();
    
    const title = titleInput.value.trim();
    const description = descriptionInput.value.trim();
    
    if (!title) {
        alert('Please enter a task title');
        return;
    }
    
    const taskData = { title, description };
    
    try {
        const response = await fetch(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create task');
        }
        
        // Clear form
        titleInput.value = '';
        descriptionInput.value = '';
        
        // Refresh data
        loadTasks();
        loadAnalytics();
        
        // Provide feedback
        showNotification('Task created successfully!');
    } catch (error) {
        console.error('Error creating task:', error);
        showNotification('Failed to create task. Please try again.', 'error');
    }
}

async function completeTask(e) {
    const taskId = e.target.getAttribute('data-id') || e.target.parentElement.getAttribute('data-id');
    
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
            method: 'PATCH'
        });
        
        if (!response.ok) {
            throw new Error('Failed to complete task');
        }
        
        // Refresh data
        loadTasks();
        loadAnalytics();
        
        // Provide feedback
        showNotification('Task marked as complete!');
    } catch (error) {
        console.error('Error completing task:', error);
        showNotification('Failed to complete task. Please try again.', 'error');
    }
}

async function deleteTask(e) {
    const taskId = e.target.getAttribute('data-id') || e.target.parentElement.getAttribute('data-id');
    
    if (confirm('Are you sure you want to delete this task?')) {
        try {
            const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete task');
            }
            
            // Refresh data
            loadTasks();
            loadAnalytics();
            
            // Provide feedback
            showNotification('Task deleted successfully!');
        } catch (error) {
            console.error('Error deleting task:', error);
            showNotification('Failed to delete task. Please try again.', 'error');
        }
    }
}

async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics/completion`);
        
        if (!response.ok) {
            throw new Error('Failed to load analytics');
        }
        
        const analytics = await response.json();
        
        totalTasksElement.textContent = analytics.total_tasks;
        completedTasksElement.textContent = analytics.completed_tasks;
        pendingTasksElement.textContent = analytics.pending_tasks;
        completionPercentageElement.textContent = `${analytics.completion_percentage}%`;
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        // Don't show notification for this to avoid overwhelming the user
    }
}

// Helper Functions
function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles inline since there's no CSS for it yet
    Object.assign(notification.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        backgroundColor: type === 'success' ? '#34a853' : '#ea4335',
        color: 'white',
        padding: '12px 20px',
        borderRadius: '4px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        zIndex: '1000',
        transition: 'transform 0.3s, opacity 0.3s',
        transform: 'translateY(100px)',
        opacity: '0'
    });
    
    // Add to body
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
        notification.style.opacity = '1';
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateY(100px)';
        notification.style.opacity = '0';
        
        // Remove from DOM after animation
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}