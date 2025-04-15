const API_BASE_URL = '/api/tasks';

async function fetchTasks() {
  try {
    const response = await fetch(API_BASE_URL);
    const tasks = await response.json();
    renderTasks(tasks);
  } catch (err) {
    console.error('Error fetching tasks:', err);
  }
}

function renderTasks(tasks) {
  const container = document.getElementById('tasks-container');
  container.innerHTML = '';

  if (tasks.length === 0) {
    container.innerHTML = '<p>No tasks found.</p>';
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
    completeBtn.onclick = () => completeTask(task.RowKey);

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '🗑';
    deleteBtn.onclick = () => deleteTask(task.RowKey);

    taskDiv.appendChild(title);
    taskDiv.appendChild(completeBtn);
    taskDiv.appendChild(deleteBtn);

    container.appendChild(taskDiv);
  });
}

async function completeTask(id) {
  try {
    await fetch(`${API_BASE_URL}/${id}/complete`, {
      method: 'PATCH'
    });
    await fetchTasks();
  } catch (err) {
    console.error('Error completing task:', err);
  }
}

async function deleteTask(id) {
  try {
    await fetch(`${API_BASE_URL}/${id}`, {
      method: 'DELETE'
    });
    await fetchTasks();
  } catch (err) {
    console.error('Error deleting task:', err);
  }
}

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

window.onload = fetchTasks;
