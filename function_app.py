import logging
import azure.functions as func
import uuid
import json
from datetime import datetime
import os
from azure.data.tables import TableServiceClient, TableEntity

app = func.FunctionApp()

TABLE_NAME = "TasksTable"

def get_table_client():
    connection_string = os.getenv("AZURE_TABLES_CONNECTION_STRING", "UseDevelopmentStorage=true")
    service = TableServiceClient.from_connection_string(conn_str=connection_string)
    return service.get_table_client(table_name=TABLE_NAME)

@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("create_task function triggered")
    try:
        req_body = req.get_json()
        task_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        entity = {
            "PartitionKey": "Task",
            "RowKey": task_id,
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": created_at,
            "completed_at": None
        }

        table_client = get_table_client()
        table_client.create_entity(entity=entity)

        logging.info(f"Task created with ID: {task_id}")
        return func.HttpResponse(json.dumps({"id": task_id, **entity}), status_code=201)

    except Exception as e:
        logging.error(f"Exception in create_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_tasks function triggered")
    try:
        table_client = get_table_client()
        status_filter = req.params.get("status")

        tasks = []
        for entity in table_client.list_entities():
            task = dict(entity)
            if not status_filter or task["status"] == status_filter:
                tasks.append(task)

        return func.HttpResponse(json.dumps(tasks), status_code=200)

    except Exception as e:
        logging.error(f"Exception in get_tasks: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_task_by_id function triggered")
    task_id = req.route_params.get("id")

    try:
        table_client = get_table_client()
        task = table_client.get_entity(partition_key="Task", row_key=task_id)
        return func.HttpResponse(json.dumps(dict(task)), status_code=200)

    except Exception as e:
        logging.error(f"Task not found or error occurred: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("update_task function triggered")
    task_id = req.route_params.get("id")

    try:
        req_body = req.get_json()
        table_client = get_table_client()
        task = table_client.get_entity(partition_key="Task", row_key=task_id)

        task["title"] = req_body.get("title", task["title"])
        task["description"] = req_body.get("description", task["description"])
        task["status"] = req_body.get("status", task["status"])

        table_client.update_entity(mode="merge", entity=task)
        return func.HttpResponse(json.dumps(dict(task)), status_code=200)

    except Exception as e:
        logging.error(f"Error updating task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("complete_task function triggered")
    task_id = req.route_params.get("id")

    try:
        table_client = get_table_client()
        task = table_client.get_entity(partition_key="Task", row_key=task_id)

        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()

        table_client.update_entity(mode="merge", entity=task)
        return func.HttpResponse(json.dumps(dict(task)), status_code=200)

    except Exception as e:
        logging.error(f"Error completing task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("delete_task function triggered")
    task_id = req.route_params.get("id")

    try:
        table_client = get_table_client()
        table_client.delete_entity(partition_key="Task", row_key=task_id)
        return func.HttpResponse("Task deleted", status_code=200)

    except Exception as e:
        logging.error(f"Error deleting task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="analytics/completion", methods=["GET"])
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("task_completion_stats function triggered")

    try:
        table_client = get_table_client()
        tasks = [dict(t) for t in table_client.list_entities()]
        completed = [t for t in tasks if t["status"] == "completed"]

        avg_time = 0
        if completed:
            total = 0
            for t in completed:
                created = datetime.fromisoformat(t["created_at"])
                completed_at = datetime.fromisoformat(t["completed_at"])
                total += (completed_at - created).total_seconds()
            avg_time = total / len(completed) / 60  # in minutes

        stats = {
            "completion_rate": (len(completed) / len(tasks)) * 100 if tasks else 0,
            "average_completion_time_minutes": round(avg_time, 2)
        }
        return func.HttpResponse(json.dumps(stats), status_code=200)

    except Exception as e:
        logging.error(f"Error getting completion stats: {str(e)}")
        return func.HttpResponse("Error", status_code=500)

@app.route(route="analytics/productivity", methods=["GET"])
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("productivity_metrics function triggered")

    try:
        table_client = get_table_client()
        tasks = [dict(t) for t in table_client.list_entities()]
        created = len(tasks)
        completed = len([t for t in tasks if t["status"] == "completed"])

        avg_time = 0
        completed_tasks = [t for t in tasks if t["status"] == "completed"]
        if completed_tasks:
            total = sum([
                (datetime.fromisoformat(t["completed_at"]) - datetime.fromisoformat(t["created_at"])).total_seconds()
                for t in completed_tasks
            ])
            avg_time = total / len(completed_tasks) / 60  # in minutes

        metrics = {
            "tasks_created": created,
            "tasks_completed": completed,
            "completion_rate": (completed / created) * 100 if created else 0,
            "average_completion_time_minutes": round(avg_time, 2)
        }
        return func.HttpResponse(json.dumps(metrics), status_code=200)

    except Exception as e:
        logging.error(f"Error calculating productivity metrics: {str(e)}")
        return func.HttpResponse("Error", status_code=500)
