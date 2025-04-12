const apiUrl = "/api/tasks";

async function fetchTasks(status = "") {
  const url = status ? `${apiUrl}?status=${status}` : apiUrl;
  const res = await fetch(url);
  const tasks = await res.json();
  renderTasks(tasks);
}

function renderTasks(tasks) {
  const list = document.getElementById("task-list");
  list.innerHTML = "";

  tasks.forEach(task => {
    const li = document.createElement("li");
    li.className = "task-item";
    li.innerHTML = `
      <strong>${task.title}</strong><br/>
      <small>${task.status}</small><br/>
      <em>${task.description}</em><br/>
      <small>Created: ${new Date(task.created_at).toLocaleString()}</small><br/>
      ${task.completed_at ? `<small>Completed: ${new Date(task.completed_at).toLocaleString()}</small><br/>` : ""}
      <div class="actions">
        <button onclick="markComplete('${task.id}')">✅ Complete</button>
        <button onclick="deleteTask('${task.id}')">🗑 Delete</button>
      </div>
    `;
    list.appendChild(li);
  });
}

async function markComplete(id) {
  await fetch(`${apiUrl}/${id}/complete`, { method: "PATCH" });
  fetchTasks();
}

async function deleteTask(id) {
  await fetch(`${apiUrl}/${id}`, { method: "DELETE" });
  fetchTasks();
}

document.getElementById("task-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = document.getElementById("title").value.trim();
  const description = document.getElementById("description").value.trim();

  if (title === "") return;

  await fetch(apiUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description }),
  });

  e.target.reset();
  fetchTasks();
});

document.getElementById("status-filter").addEventListener("change", (e) => {
  fetchTasks(e.target.value);
});

async function fetchAnalytics() {
  const res1 = await fetch("/api/analytics/completion");
  const stats1 = await res1.json();
  const res2 = await fetch("/api/analytics/productivity");
  const stats2 = await res2.json();

  document.getElementById("completion-rate").textContent = `Completion Rate: ${stats1.completion_rate}%`;
  document.getElementById("avg-completion").textContent = `Avg Completion Time: ${stats1.average_completion_time_minutes} min`;
  document.getElementById("tasks-created").textContent = `Tasks Created: ${stats2.tasks_created}`;
  document.getElementById("tasks-completed").textContent = `Tasks Completed: ${stats2.tasks_completed}`;
}

fetchTasks();
fetchAnalytics();
