import logging
import azure.functions as func
from datetime import datetime
import json
import uuid

app = func.FunctionApp()

# In-memory task list (to be replaced with Azure Table Storage)
tasks = []

@app.route(route="tasks", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("create_task function triggered")

    try:
        req_body = req.get_json()
        logging.info(f"Received payload: {req_body}")

        new_task = {
            "id": str(uuid.uuid4()),
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }

        tasks.append(new_task)
        logging.info(f"Task created successfully: {new_task}")
        return func.HttpResponse(json.dumps(new_task), status_code=201)

    except Exception as e:
        logging.error(f"Exception in create_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_tasks function triggered")

    try:
        status_filter = req.params.get("status")
        logging.info(f"Status filter: {status_filter}")

        if status_filter:
            filtered_tasks = [task for task in tasks if task["status"] == status_filter]
            logging.info(f"Found {len(filtered_tasks)} tasks with status '{status_filter}'")
            return func.HttpResponse(json.dumps(filtered_tasks), status_code=200)

        logging.info(f"Returning all {len(tasks)} tasks")
        return func.HttpResponse(json.dumps(tasks), status_code=200)

    except Exception as e:
        logging.error(f"Exception in get_tasks: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_task_by_id function triggered")

    try:
        task_id = req.route_params.get("id")
        logging.info(f"Looking for task ID: {task_id}")

        task = next((t for t in tasks if t["id"] == task_id), None)

        if task:
            logging.info(f"Task found: {task_id}")
            return func.HttpResponse(json.dumps(task), status_code=200)
        else:
            logging.warning(f"Task not found: {task_id}")
            return func.HttpResponse("Task not found", status_code=404)

    except Exception as e:
        logging.error(f"Exception in get_task_by_id: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("update_task function triggered")

    try:
        task_id = req.route_params.get("id")
        req_body = req.get_json()
        logging.info(f"Updating task ID: {task_id} with data: {req_body}")

        task = next((t for t in tasks if t["id"] == task_id), None)

        if task:
            task.update({
                "title": req_body.get("title", task["title"]),
                "description": req_body.get("description", task["description"]),
                "status": req_body.get("status", task["status"])
            })
            logging.info(f"Task updated: {task}")
            return func.HttpResponse(json.dumps(task), status_code=200)

        logging.warning(f"Task not found for update: {task_id}")
        return func.HttpResponse("Task not found", status_code=404)

    except Exception as e:
        logging.error(f"Exception in update_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}/complete", methods=["PATCH"], auth_level=func.AuthLevel.ANONYMOUS)
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("complete_task function triggered")

    try:
        task_id = req.route_params.get("id")
        task = next((t for t in tasks if t["id"] == task_id), None)

        if task:
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            logging.info(f"Task marked complete: {task}")
            return func.HttpResponse(json.dumps(task), status_code=200)

        logging.warning(f"Task not found for completion: {task_id}")
        return func.HttpResponse("Task not found", status_code=404)

    except Exception as e:
        logging.error(f"Exception in complete_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("delete_task function triggered")

    try:
        task_id = req.route_params.get("id")
        logging.info(f"Deleting task with ID: {task_id}")

        global tasks
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                deleted_task = tasks.pop(i)
                logging.info(f"Task deleted: {deleted_task}")
                return func.HttpResponse(json.dumps({
                    "message": "Task deleted successfully",
                    "task": deleted_task
                }), status_code=200)

        logging.warning(f"Task not found for deletion: {task_id}")
        return func.HttpResponse("Task not found", status_code=404)

    except Exception as e:
        logging.error(f"Exception in delete_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="analytics/completion", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("task_completion_stats function triggered")

    try:
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t["status"] == "completed")
        pending = total_tasks - completed
        percentage = (completed / total_tasks * 100) if total_tasks > 0 else 0.0

        stats = {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "completion_percentage": round(percentage, 2)
        }

        logging.info(f"Task stats calculated: {stats}")
        return func.HttpResponse(json.dumps(stats), status_code=200)

    except Exception as e:
        logging.error(f"Exception in task_completion_stats: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="analytics/productivity", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("productivity_metrics function triggered")

    try:
        completed_tasks = [t for t in tasks if t["status"] == "completed"]
        logging.info(f"{len(completed_tasks)} completed tasks found")

        if not completed_tasks:
            return func.HttpResponse(json.dumps({
                "message": "No completed tasks yet",
                "average_completion_time_minutes": None,
                "completion_rate": 0
            }), status_code=200)

        total_time = 0
        count = 0

        for t in completed_tasks:
            created = datetime.fromisoformat(t["created_at"])
            completed = datetime.fromisoformat(t["completed_at"])
            duration = (completed - created).total_seconds() / 60
            total_time += duration
            count += 1

        avg_completion = total_time / count
        completion_rate = (count / len(tasks)) * 100 if tasks else 0

        metrics = {
            "tasks_created": len(tasks),
            "tasks_completed": len(completed_tasks),
            "average_completion_time_minutes": round(avg_completion, 2),
            "average_completion_time_hours": round(avg_completion / 60, 2),
            "completion_rate": round(completion_rate, 2)
        }

        logging.info(f"Productivity metrics: {metrics}")
        return func.HttpResponse(json.dumps(metrics), status_code=200)

    except Exception as e:
        logging.error(f"Exception in productivity_metrics: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)
