const API_BASE_URL = 'https://myfunctionappz.azurewebsites.net/api/tasks';

async function fetchTasks() {
  const response = await fetch(API_BASE_URL);
  const tasks = await response.json();
  displayTasks(tasks);
}

function displayTasks(tasks) {
  const container = document.getElementById('tasks-container');
  container.innerHTML = '';

  if (tasks.length === 0) {
    container.innerHTML = '<p style="text-align:center; color:#6b7280; font-style:italic;">No tasks yet. Start by creating one above!</p>';
    return;
  }

  tasks.forEach(task => {
    const taskDiv = document.createElement('div');
    taskDiv.className = `task ${task.status}`;

    
    const topRow = document.createElement('div');
    topRow.style.display = 'flex';
    topRow.style.justifyContent = 'space-between';
    topRow.style.alignItems = 'center';

    const title = document.createElement('span');
    title.innerHTML = `<strong>${task.title}</strong>`;
    if (task.status === 'completed') {
      title.style.textDecoration = 'line-through';
    }

    const badge = document.createElement('span');
    badge.className = `status-tag ${task.status}`;
    badge.textContent = task.status.charAt(0).toUpperCase() + task.status.slice(1);

    topRow.appendChild(title);
    topRow.appendChild(badge);

    
    const date = document.createElement('div');
    const createdDate = new Date(task.created_at).toLocaleString();
    date.className = 'task-date';
    date.textContent = `Created: ${createdDate}`;

    
    const completeBtn = document.createElement('button');
    completeBtn.textContent = 'Mark Task as Complete';
    completeBtn.disabled = task.status === 'completed';
    completeBtn.onclick = () => completeTask(task.id);

    
    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete Task';
    deleteBtn.onclick = () => deleteTask(task.id);

    
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'button-group';
    buttonGroup.appendChild(completeBtn);
    buttonGroup.appendChild(deleteBtn);

    
    taskDiv.appendChild(topRow);
    taskDiv.appendChild(date);
    taskDiv.appendChild(buttonGroup);
    container.appendChild(taskDiv);
  });
}

async function completeTask(id) {
  await fetch(`${API_BASE_URL}/${id}/complete`, {
    method: 'PATCH'
  });
  fetchTasks();
}

async function deleteTask(id) {
  await fetch(`${API_BASE_URL}/${id}`, {
    method: 'DELETE'
  });
  fetchTasks();
}

window.onload = fetchTasks;


document.getElementById('task-form').addEventListener('submit', async function (e) {
  e.preventDefault();

  const title = document.getElementById('title').value.trim();
  const description = document.getElementById('description').value.trim();

  if (!title) {
    alert('Title is required!');
    return;
  }

  const task = { title, description };

  try {
    const res = await fetch(API_BASE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task)
    });

    if (!res.ok) throw new Error('Failed to create task');

    document.getElementById('title').value = '';
    document.getElementById('description').value = '';
    await fetchTasks(); 
  } catch (err) {
    console.error(err);
    alert('Error creating task.');
  }
});

const ANALYTICS_BASE_URL = 'https://myfunctionappz.azurewebsites.net/api/analytics';

async function fetchProductivityMetrics() {
  try {
    const res = await fetch(`${ANALYTICS_BASE_URL}/productivity`);
    if (!res.ok) throw new Error('Failed to fetch productivity metrics');
    const data = await res.json();

    const container = document.getElementById('analytics-container');
    container.innerHTML = `
      <h2 style="text-align:center;">📈 Productivity Metrics</h2>
      <ul style="list-style-type:none; padding:0;">
        <li><strong>Tasks Created:</strong> ${data.tasks_created}</li>
        <li><strong>Tasks Completed:</strong> ${data.tasks_completed}</li>
        <li><strong>Completion Rate:</strong> ${data.completion_rate}%</li>
        <li><strong>Average Completion Time:</strong> ${data.average_completion_time_minutes} minutes</li>
      </ul>
    `;
  } catch (err) {
    console.error(err);
    alert('Error fetching productivity metrics.');
  }
}

async function fetchTaskCompletionStats() {
  try {
    const res = await fetch(`${ANALYTICS_BASE_URL}/completion`);
    if (!res.ok) throw new Error('Failed to fetch task completion stats');
    const data = await res.json();

    const container = document.getElementById('analytics-container');
    container.innerHTML = `
      <h2 style="text-align:center;">📊 Task Completion Stats</h2>
      
      <div class="metric-center">
        <div class="circle-chart">
          <svg viewBox="0 0 36 36" class="circular-chart green">
            <path class="circle-bg"
              d="M18 2.0845
                 a 15.9155 15.9155 0 0 1 0 31.831
                 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path class="circle"
              stroke-dasharray="${data.tasks_completed_today * 10}, 100"
              d="M18 2.0845
                 a 15.9155 15.9155 0 0 1 0 31.831
                 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <text x="18" y="20.35" class="percentage">${data.tasks_completed_today}</text>
          </svg>
          <div class="chart-label">Tasks Completed Today</div>
        </div>
      </div>
    `;
  } catch (err) {
    console.error(err);
    alert('Error fetching completion stats.');
  }
}



document.getElementById('productivity-btn').addEventListener('click', fetchProductivityMetrics);
document.getElementById('completion-btn').addEventListener('click', fetchTaskCompletionStats);

