const apiBaseUrl = "https://myfunctionappz.azurewebsites.net/api"; // ✅ HTTPS to avoid mixed content errors

window.onload = () => {
  const form = document.getElementById("create-task-form");
  const filter = document.getElementById("filter-status");

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const title = document.getElementById("title").value.trim();
      const description = document.getElementById("description").value.trim();
      if (!title) return;

      try {
        const response = await fetch(`${apiBaseUrl}/tasks`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description }),
        });

        if (response.ok) {
          document.getElementById("title").value = "";
          document.getElementById("description").value = "";
          await fetchTasks();
          await fetchAnalytics();
        } else {
          console.error("Error creating task:", await response.text());
        }
      } catch (error) {
        console.error("Error creating task:", error);
      }
    });
  }

  if (filter) {
    filter.addEventListener("change", fetchTasks);
  }

  fetchTasks();
  fetchAnalytics();
};

async function fetchTasks() {
  try {
    const status = document.getElementById("filter-status")?.value;
    let url = `${apiBaseUrl}/tasks`;
    if (status && status !== "all") {
      url += `?status=${status}`;
    }

    const response = await fetch(url);
    const tasks = await response.json();

    const taskList = document.getElementById("task-list");
    taskList.innerHTML = "";

    tasks.forEach((task) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>${task.title}</strong> - ${task.status}
        <button onclick="completeTask('${task.id}')">✅</button>
        <button onclick="deleteTask('${task.id}')">🗑️</button>
      `;
      taskList.appendChild(li);
    });
  } catch (error) {
    console.error("Error fetching tasks:", error);
  }
}

async function completeTask(id) {
  try {
    await fetch(`${apiBaseUrl}/tasks/${id}/complete`, {
      method: "PATCH",
    });
    await fetchTasks();
    await fetchAnalytics();
  } catch (error) {
    console.error("Error completing task:", error);
  }
}

async function deleteTask(id) {
  try {
    await fetch(`${apiBaseUrl}/tasks/${id}`, {
      method: "DELETE",
    });
    await fetchTasks();
    await fetchAnalytics();
  } catch (error) {
    console.error("Error deleting task:", error);
  }
}

async function fetchAnalytics() {
  try {
    const response = await fetch(`${apiBaseUrl}/analytics/productivity`);
    const stats = await response.json();

    document.getElementById("completion-rate").textContent = `${stats.completion_rate || 0}%`;
    document.getElementById("avg-time").textContent = `${stats.average_completion_time_minutes || 0} mins`;
    document.getElementById("tasks-created").textContent = stats.tasks_created || 0;
    document.getElementById("tasks-completed").textContent = stats.tasks_completed || 0;
  } catch (error) {
    console.error("Error fetching analytics:", error);
  }
}
