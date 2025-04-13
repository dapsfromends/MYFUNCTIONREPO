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
    }
  
    if (filter) {
      filter.addEventListener("change", fetchTasks);
    }
  
    fetchTasks();
    fetchAnalytics();
  };
  