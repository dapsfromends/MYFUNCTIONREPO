const apiBaseUrl = "https://myfunctionappz.azurewebsites.net/api";

// Create task
document.getElementById("create-task-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("title").value.trim();
    const description = document.getElementById("description").value.trim();

    if (!title) return;

    try {
        const response = await fetch(`${apiBaseUrl}/tasks`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, description })
        });
        if (response.ok) {
            document.getElementById("title").value = "";
            document.getElementById("description").value = "";
            await fetchTasks();
            await fetchAnalytics();
        }
    } catch (error) {
        console.error("Error creating task:", error);
    }
});

// Fetch all tasks
async function fetchTasks() {
    const filter = document.getElementById("filter-status").value;
    let url = `${apiBaseUrl}/tasks`;
    if (filter !== "all") {
        url += `?status=${filter}`;
    }

    try {
        const response = await fetch(url);
        const tasks = await response.json();
        renderTasks(tasks);
    } catch (error) {
        console.error("Error fetching tasks:", error);
    }
}

// Render tasks
function renderTasks(tasks) {
    const container = document.getElementById("task-list");
    container.innerHTML = "";
    tasks.forEach((task) => {
        const div = document.createElement("div");
        div.className = "task-item";
        div.innerHTML = `
            <h4>${task.title}</h4>
            <p>${task.description}</p>
            <p>Status: ${task.status}</p>
            <button onclick="completeTask('${task.id}')">Complete</button>
            <button onclick="deleteTask('${task.id}')">Delete</button>
        `;
        container.appendChild(div);
    });
}

// Complete a task
async function completeTask(id) {
    try {
        const response = await fetch(`${apiBaseUrl}/tasks/${id}/complete`, {
            method: "PATCH"
        });
        if (response.ok) {
            await fetchTasks();
            await fetchAnalytics();
        }
    } catch (error) {
        console.error("Error completing task:", error);
    }
}

// Delete a task
async function deleteTask(id) {
    try {
        const response = await fetch(`${apiBaseUrl}/tasks/${id}`, {
            method: "DELETE"
        });
        if (response.ok) {
            await fetchTasks();
            await fetchAnalytics();
        }
    } catch (error) {
        console.error("Error deleting task:", error);
    }
}

// Filter by status
document.getElementById("filter-status").addEventListener("change", fetchTasks);

// Fetch analytics
async function fetchAnalytics() {
    try {
        const response = await fetch(`${apiBaseUrl}/analytics/productivity`);
        const data = await response.json();
        document.getElementById("completion-rate").textContent = data.completion_rate + "%";
        document.getElementById("avg-time").textContent = data.average_completion_time_minutes + " mins";
        document.getElementById("created-count").textContent = data.tasks_created;
        document.getElementById("completed-count").textContent = data.tasks_completed;
    } catch (error) {
        console.error("Error fetching analytics:", error);
    }
}

window.onload = () => {
    fetchTasks();
    fetchAnalytics();
};
