import azure.functions as func
import logging
import json
import uuid
from datetime import datetime

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

tasks = []

# Create a new task
@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Create Task function processed a request.')
    
    try:
        req_body = req.get_json()
        logging.info(f'Request body: {req_body}')
        if not req_body or 'title' not in req_body:
            logging.warning('Missing required field: title')
            return func.HttpResponse(
                "Please include a title in your request",
                status_code=400
            )
        new_task = {
            "id": str(uuid.uuid4()),
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        logging.info(f'Created task with ID: {new_task["id"]}, Title: "{new_task["title"]}"')
        tasks.append(new_task)
        
        return func.HttpResponse(
            json.dumps(new_task),
            mimetype="application/json",
            status_code=201
        )
        
    except ValueError as e:
        logging.error(f'Invalid request format: {str(e)}')
        return func.HttpResponse(
            "Invalid request format. Please check your JSON syntax.",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            "An unexpected error occurred",
            status_code=500
        )

# Get all tasks
@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Get Tasks function processed a request.')
    
    # Get status filter if provided
    status = req.params.get('status')
    logging.info(f'Status filter applied: {status if status else "none"}')
    
    if status:
        filtered_tasks = [task for task in tasks if task['status'] == status]
        logging.info(f'Found {len(filtered_tasks)} tasks matching status "{status}"')
        return func.HttpResponse(
            json.dumps(filtered_tasks),
            mimetype="application/json"
        )
    else:
        logging.info(f'Returning all {len(tasks)} tasks')
        return func.HttpResponse(
            json.dumps(tasks),
            mimetype="application/json"
        )

# Get task by ID
@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Get Task by ID function processed a request.')
    
    task_id = req.route_params.get('id')
    logging.info(f'Looking for task ID: {task_id}')
    
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if task:
        logging.info(f'Found task: "{task["title"]}"')
        return func.HttpResponse(
            json.dumps(task),
            mimetype="application/json"
        )
    else:
        logging.warning(f'Task with ID {task_id} not found')
        return func.HttpResponse(
            "Task not found",
            status_code=404
        )

# Update task
@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Update Task function processed a request.')
    
    task_id = req.route_params.get('id')
    logging.info(f'Updating task with ID: {task_id}')
    
    try:
        req_body = req.get_json()
        logging.info(f'Update data: {req_body}')
        
        task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
        
        if task_index is None:
            logging.warning(f'Task with ID {task_id} not found for update')
            return func.HttpResponse(
                "Task not found",
                status_code=404
            )
        
        current_task = tasks[task_index]
        updated_task = {
            "id": current_task["id"],
            "title": req_body.get("title", current_task["title"]),
            "description": req_body.get("description", current_task["description"]),
            "status": req_body.get("status", current_task["status"]),
            "created_at": current_task["created_at"],
            "completed_at": current_task["completed_at"]
        }
        
        tasks[task_index] = updated_task
        logging.info(f'Successfully updated task: "{updated_task["title"]}"')
        
        return func.HttpResponse(
            json.dumps(updated_task),
            mimetype="application/json"
        )
        
    except ValueError:
        logging.error('Invalid request format')
        return func.HttpResponse(
            "Invalid request format. Please check your JSON syntax.",
            status_code=400
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            "An unexpected error occurred",
            status_code=500
        )

# Delete task
@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Delete Task function processed a request.')
    
    task_id = req.route_params.get('id')
    logging.info(f'Attempting to delete task with ID: {task_id}')
    
    task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
    
    if task_index is None:
        logging.warning(f'Task with ID {task_id} not found for deletion')
        return func.HttpResponse(
            "Task not found",
            status_code=404
        )
    
    deleted_task = tasks.pop(task_index)
    logging.info(f'Successfully deleted task: "{deleted_task["title"]}"')
    
    return func.HttpResponse(
        json.dumps({"message": "Task deleted successfully", "task": deleted_task}),
        mimetype="application/json"
    )

# Mark task as complete
@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Complete Task function processed a request.')
    
    task_id = req.route_params.get('id')
    logging.info(f'Marking task with ID {task_id} as complete')
    
    task_index = next((i for i, t in enumerate(tasks) if t['id'] == task_id), None)
    
    if task_index is None:
        logging.warning(f'Task with ID {task_id} not found for completion')
        return func.HttpResponse("Task not found", status_code=404)
    
    tasks[task_index]["status"] = "completed"
    tasks[task_index]["completed_at"] = datetime.now().isoformat()
    logging.info(f'Successfully completed task: "{tasks[task_index]["title"]}"')
    
    return func.HttpResponse(json.dumps(tasks[task_index]), mimetype="application/json")

# Completion stats
@app.route(route="analytics/completion", methods=["GET"])
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("task_completion_stats function triggered.")
    
    try:
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t["status"] == "completed"])
        pending_tasks = total_tasks - completed_tasks
        completion_percentage = (completed_tasks / total_tasks) * 100 if total_tasks else 0

        logging.info(f"Completion Stats: {completed_tasks} completed out of {total_tasks}")

        result = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "completion_percentage": round(completion_percentage, 2)
        }

        return func.HttpResponse(json.dumps(result), mimetype="application/json")
    
    except Exception as e:
        logging.error(f"Error in task_completion_stats: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="analytics/productivity", methods=["GET"])
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("productivity_metrics function triggered.")

    try:
        today = datetime.now().date()
        tasks_created = len(tasks)
        tasks_completed = len([t for t in tasks if t["status"] == "completed"])
        completed_today = len([
            t for t in tasks if t["status"] == "completed" and
            t.get("completed_at") and datetime.fromisoformat(t["completed_at"]).date() == today
        ])

        completion_rate = (tasks_completed / tasks_created) * 100 if tasks_created else 0

        result = {
            "tasks_created": tasks_created,
            "tasks_completed": tasks_completed,
            "completion_rate": round(completion_rate, 2),
            "tasks_completed_today": completed_today,
            "average_completion_time_hours": avg_completion_time_hours
        }

        logging.info(f"Productivity metrics calculated: {result}")
        return func.HttpResponse(json.dumps(result), mimetype="application/json")

    except Exception as e:
        logging.error(f"Error calculating productivity metrics: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)
