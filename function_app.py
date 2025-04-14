import logging
import json
import os
import uuid
from datetime import datetime, timedelta

import azure.functions as func
from azure.data.tables import TableServiceClient, TableEntity
from azure.core.exceptions import ResourceNotFoundError

app = func.FunctionApp() 

TABLE_NAME = "TasksTable"

from azure.core.exceptions import ResourceExistsError

def get_table_client():
    connection_string = os.getenv("AZURE_TABLES_CONNECTION_STRING")
    service = TableServiceClient.from_connection_string(conn_str=connection_string)
    try:
        service.create_table_if_not_exists("TasksTable")
    except ResourceExistsError:
        pass
    return service.get_table_client("TasksTable")

@app.function_name(name="create_task")
@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("create_task function triggered")
    try:
        data = json.loads(req.get_body())
        title = data.get("title")
        description = data.get("description")

        if not title:
            return func.HttpResponse("Missing 'title'", status_code=400)

        task_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        entity = {
            "PartitionKey": "task",
            "RowKey": task_id,
            "title": title,
            "description": description or "",
            "status": "pending",
            "created_at": now,
            "completed_at": None
        }

        table = get_table_client()
        table.create_entity(entity=entity)

        return func.HttpResponse(json.dumps(entity), status_code=201, mimetype="application/json")

    except Exception as e:
        logging.error(f"Exception in create_task: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

@app.function_name(name="get_tasks")
@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_tasks function triggered")
    try:
        status_filter = req.params.get("status")
        table = get_table_client()
        query = "PartitionKey eq 'task'"
        if status_filter:
            query += f" and status eq '{status_filter}'"

        tasks = list(table.query_entities(query))
        for task in tasks:
            task["id"] = task.pop("RowKey")

        return func.HttpResponse(json.dumps(tasks), status_code=200, mimetype="application/json")

    except Exception as e:
        logging.error(f"Exception in get_tasks: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

@app.function_name(name="get_task_by_id")
@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    task_id = req.route_params.get("id")
    logging.info(f"get_task_by_id triggered for ID {task_id}")
    try:
        table = get_table_client()
        task = table.get_entity("task", task_id)
        task["id"] = task.pop("RowKey")
        return func.HttpResponse(json.dumps(task), status_code=200, mimetype="application/json")
    except ResourceNotFoundError:
        return func.HttpResponse("Task not found", status_code=404)
    except Exception as e:
        logging.error(f"Task not found or error: {e}")
        return func.HttpResponse("Error retrieving task", status_code=404)

@app.function_name(name="update_task")
@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    task_id = req.route_params.get("id")
    logging.info(f"update_task triggered for ID {task_id}")
    try:
        data = json.loads(req.get_body())
        table = get_table_client()
        task = table.get_entity("task", task_id)

        task["title"] = data.get("title", task["title"])
        task["description"] = data.get("description", task["description"])
        task["status"] = data.get("status", task["status"])
        table.update_entity(mode="MERGE", entity=task)

        task["id"] = task.pop("RowKey")
        return func.HttpResponse(json.dumps(task), status_code=200, mimetype="application/json")
    except ResourceNotFoundError:
        return func.HttpResponse("Task not found", status_code=404)
    except Exception as e:
        logging.error(f"Error updating task: {e}")
        return func.HttpResponse("Error updating task", status_code=404)

@app.function_name(name="complete_task")
@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    task_id = req.route_params.get("id")
    logging.info(f"complete_task triggered for ID {task_id}")
    try:
        table = get_table_client()
        task = table.get_entity("task", task_id)
        task["status"] = "completed"
        task["completed_at"] = datetime.utcnow().isoformat()
        table.update_entity(mode="MERGE", entity=task)

        task["id"] = task.pop("RowKey")
        return func.HttpResponse(json.dumps(task), status_code=200, mimetype="application/json")
    except ResourceNotFoundError:
        return func.HttpResponse("Task not found", status_code=404)
    except Exception as e:
        logging.error(f"Error completing task: {e}")
        return func.HttpResponse("Error completing task", status_code=404)

@app.function_name(name="delete_task")
@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    task_id = req.route_params.get("id")
    logging.info(f"delete_task triggered for ID {task_id}")
    try:
        table = get_table_client()
        table.delete_entity("task", task_id)
        return func.HttpResponse(status_code=200)
    except ResourceNotFoundError:
        return func.HttpResponse("Task not found", status_code=404)
    except Exception as e:
        logging.error(f"Error deleting task: {e}")
        return func.HttpResponse("Error deleting task", status_code=404)

@app.function_name(name="task_completion_stats")
@app.route(route="analytics/completion", methods=["GET"])
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("task_completion_stats triggered")
    try:
        table = get_table_client()
        all_tasks = list(table.query_entities("PartitionKey eq 'task'"))

        completed = [t for t in all_tasks if t.get("status") == "completed"]
        today = datetime.utcnow().date()
        completed_today = [
            t for t in completed if datetime.fromisoformat(t["completed_at"]).date() == today
        ]

        result = {
            "tasks_completed_today": len(completed_today)
        }
        return func.HttpResponse(json.dumps(result), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error getting completion stats: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

@app.function_name(name="productivity_metrics")
@app.route(route="analytics/productivity", methods=["GET"])
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("productivity_metrics triggered")
    try:
        table = get_table_client()
        all_tasks = list(table.query_entities("PartitionKey eq 'task'"))
        created_count = len(all_tasks)
        completed_tasks = [t for t in all_tasks if t.get("status") == "completed"]
        completed_count = len(completed_tasks)

        completion_times = []
        for t in completed_tasks:
            try:
                created = datetime.fromisoformat(t["created_at"])
                completed = datetime.fromisoformat(t["completed_at"])
                completion_times.append((completed - created).total_seconds() / 60)
            except:
                continue

        avg_minutes = sum(completion_times) / len(completion_times) if completion_times else 0
        rate = (completed_count / created_count) * 100 if created_count else 0

        result = {
            "tasks_created": created_count,
            "tasks_completed": completed_count,
            "completion_rate": round(rate, 2),
            "average_completion_time_minutes": round(avg_minutes, 2)
        }
        return func.HttpResponse(json.dumps(result), status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error(f"Error calculating productivity metrics: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)
