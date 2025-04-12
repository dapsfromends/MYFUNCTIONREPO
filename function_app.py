import logging
import azure.functions as func
from datetime import datetime
import json
import uuid

app = func.FunctionApp()

# In-memory storage (will be replaced with Azure Table Storage)
tasks = []

@app.route(route="tasks", methods=["POST"])
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
        logging.info(f"Task created successfully: {new_task['id']}")

        return func.HttpResponse(json.dumps(new_task), status_code=201)

    except Exception as e:
        logging.error(f"Exception in create_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_tasks function triggered")

    try:
        status_filter = req.params.get("status")
        logging.info(f"Filter status: {status_filter}")

        if status_filter:
            filtered_tasks = [task for task in tasks if task["status"] == status_filter]
            logging.info(f"{len(filtered_tasks)} tasks found with status '{status_filter}'")
            return func.HttpResponse(json.dumps(filtered_tasks), status_code=200)
        else:
            logging.info(f"Returning all tasks: {len(tasks)} total")
            return func.HttpResponse(json.dumps(tasks), status_code=200)

    except Exception as e:
        logging.error(f"Exception in get_tasks: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_task_by_id function triggered")

    task_id = req.route_params.get("id")
    logging.info(f"Looking for task with ID: {task_id}")

    task = next((t for t in tasks if t["id"] == task_id), None)

    if task:
        logging.info(f"Task found: {task_id}")
        return func.HttpResponse(json.dumps(task), status_code=200)
    else:
        logging.error(f"Task not found: {task_id}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("update_task function triggered")

    task_id = req.route_params.get("id")
    logging.info(f"Attempting to update task with ID: {task_id}")

    try:
        req_body = req.get_json()
        task = next((t for t in tasks if t["id"] == task_id), None)

        if task:
            task.update({
                "title": req_body.get("title", task["title"]),
                "description": req_body.get("description", task["description"]),
                "status": req_body.get("status", task["status"])
            })
            logging.info(f"Task updated successfully: {task_id}")
            return func.HttpResponse(json.dumps(task), status_code=200)
        else:
            logging.error(f"Task not found for update: {task_id}")
            return func.HttpResponse("Task not found", status_code=404)

    except Exception as e:
        logging.error(f"Exception in update_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("complete_task function triggered")

    task_id = req.route_params.get("id")
    logging.info(f"Marking task as completed: {task_id}")

    task = next((t for t in tasks if t["id"] == task_id), None)

    if task:
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        logging.info(f"Task marked as completed: {task_id}")
        return func.HttpResponse(json.dumps(task), status_code=200)
    else:
        logging.error(f"Task not found for completion: {task_id}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("delete_task function triggered")

    task_id = req.route_params.get("id")
    logging.info(f"Attempting to delete task with ID: {task_id}")

    global tasks
    filtered_tasks = [t for t in tasks if t["id"] != task_id]

    if len(filtered_tasks) != len(tasks):
        tasks = filtered_tasks
        logging.info(f"Task deleted: {task_id}")
        return func.HttpResponse("Task deleted", status_code=200)
    else:
        logging.error(f"Task not found for deletion: {task_id}")
        return func.HttpResponse("Task not found", status_code=404)
