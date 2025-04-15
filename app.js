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
    container.innerHTML = '<p>No tasks yet.</p>';
    return;
  }

  tasks.forEach(task => {
    const taskDiv = document.createElement('div');
    taskDiv.className = 'task';

    const title = document.createElement('span');
    title.textContent = `${task.title} - ${task.status}`;
    if (task.status === 'completed') {
      title.style.textDecoration = 'line-through';
    }

    const completeBtn = document.createElement('button');
    completeBtn.textContent = '✅';
    completeBtn.disabled = task.status === 'completed';
    completeBtn.onclick = () => completeTask(task.id);

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '🗑️';
    deleteBtn.onclick = () => deleteTask(task.id);

    taskDiv.appendChild(title);
    taskDiv.appendChild(completeBtn);
    taskDiv.appendChild(deleteBtn);

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

// 👇 Add this at the bottom of app.js
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
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task)
    });

    if (!res.ok) throw new Error('Failed to create task');

    document.getElementById('title').value = '';
    document.getElementById('description').value = '';
    await loadTasks(); // refresh the task list
  } catch (err) {
    console.error(err);
    alert('Error creating task.');
  }
});

