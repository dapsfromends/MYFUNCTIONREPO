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

    // Title
    const title = document.createElement('span');
    title.innerHTML = `<strong>${task.title}</strong>`;
    if (task.status === 'completed') {
      title.style.textDecoration = 'line-through';
    }

    // ✅ Status Badge
    const statusBadge = document.createElement('span');
    statusBadge.className = `status-tag ${task.status}`;
    statusBadge.textContent = task.status.charAt(0).toUpperCase() + task.status.slice(1);

    // ✅ Creation Date
    const date = document.createElement('div');
    const createdDate = new Date(task.created_at).toLocaleString();
    date.className = 'task-date';
    date.textContent = `Created: ${createdDate}`;

    // ✅ Complete Button
    const completeBtn = document.createElement('button');
    completeBtn.textContent = '✅';
    completeBtn.disabled = task.status === 'completed';
    completeBtn.onclick = () => completeTask(task.id);

    // 🗑 Delete Button
    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = '🗑';
    deleteBtn.onclick = () => deleteTask(task.id);

    // Group title & badge together
    const topRow = document.createElement('div');
    topRow.style.display = 'flex';
    topRow.style.justifyContent = 'space-between';
    topRow.style.alignItems = 'center';
    topRow.appendChild(title);
    topRow.appendChild(statusBadge);

    taskDiv.appendChild(topRow);
    taskDiv.appendChild(date);
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

// ✅ Handle form submission
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
    await fetchTasks(); // refresh the task list
  } catch (err) {
    console.error(err);
    alert('Error creating task.');
  }
});
