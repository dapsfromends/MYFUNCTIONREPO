const API_BASE = "http://myfunctionappz.azurewebsites.net/api/tasks";

document.addEventListener("DOMContentLoaded", () => {
  fetchTasks();

  document.getElementById("taskForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("taskTitle").value;
    const description = document.getElementById("taskDescription").value;
    if (title.trim()) {
      await createTask(title, description);
      document.getElementById("taskForm").reset();
      fetchTasks();
    }
  });
});

async function fetchTasks() {
  try {
    const res = await fetch(API_BASE);
    const tasks = await res.json();

    const taskList = document.getElementById("taskList");
    taskList.innerHTML = "";

    tasks.forEach(task => {
      const li = document.createElement("li");
      li.className = `task ${task.status}`;
      li.innerHTML = `
        <h3>${task.title}</h3>
        <p>${task.description}</p>
        <p>Status: ${task.status}</p>
        <div class="task-buttons">
          ${task.status !== "completed" ? `<button onclick="completeTask('${task.id}')">Complete</button>` : ""}
          <button onclick="deleteTask('${task.id}')">Delete</button>
        </div>
      `;
      taskList.appendChild(li);
    });
  } catch (err) {
    console.error("Error fetching tasks:", err);
  }
}

async function createTask(title, description) {
  try {
    const res = await fetch(API_BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description })
    });
    return await res.json();
  } catch (err) {
    console.error("Error creating task:", err);
  }
}

async function completeTask(id) {
  try {
    await fetch(`${API_BASE}/${id}/complete`, {
      method: "PATCH"
    });
    fetchTasks();
  } catch (err) {
    console.error("Error completing task:", err);
  }
}

async function deleteTask(id) {
  try {
    await fetch(`${API_BASE}/${id}`, {
      method: "DELETE"
    });
    fetchTasks();
  } catch (err) {
    console.error("Error deleting task:", err);
  }
}
