import logging
import azure.functions as func
from azure.data.tables import TableServiceClient, TableEntity
from datetime import datetime
import os
import uuid
import json

app = func.FunctionApp()

def get_table_client():
    connection_string = os.getenv("AZURE_TABLES_CONNECTION_STRING")
    table_name = os.getenv("TABLE_NAME", "TasksTable")
    service = TableServiceClient.from_connection_string(conn_str=connection_string)
    table_client = service.get_table_client(table_name)
    return table_client

@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("create_task function triggered")
    try:
        req_body = req.get_json()
        task_id = str(uuid.uuid4())
        entity = {
            "PartitionKey": "task",
            "RowKey": task_id,
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": ""
        }
        table = get_table_client()
        table.create_entity(entity=entity)

        logging.info(f"Task created successfully: {task_id}")
        return func.HttpResponse(json.dumps({"id": task_id, **entity}), status_code=201)
    except Exception as e:
        logging.error(f"Exception in create_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_tasks function triggered")
    try:
        table = get_table_client()
        status_filter = req.params.get("status")
        entities = table.query_entities("PartitionKey eq 'task'")
        tasks = [dict(e) for e in entities]
        if status_filter:
            tasks = [t for t in tasks if t.get("status") == status_filter]
        return func.HttpResponse(json.dumps(tasks), status_code=200)
    except Exception as e:
        logging.error(f"Exception in get_tasks: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_task_by_id function triggered")
    try:
        task_id = req.route_params.get("id")
        table = get_table_client()
        entity = table.get_entity(partition_key="task", row_key=task_id)
        return func.HttpResponse(json.dumps(dict(entity)), status_code=200)
    except Exception as e:
        logging.error(f"Task not found or error occurred: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("update_task function triggered")
    try:
        task_id = req.route_params.get("id")
        req_body = req.get_json()
        table = get_table_client()
        entity = table.get_entity(partition_key="task", row_key=task_id)

        entity["title"] = req_body.get("title", entity["title"])
        entity["description"] = req_body.get("description", entity["description"])
        entity["status"] = req_body.get("status", entity["status"])

        table.update_entity(mode="replace", entity=entity)
        return func.HttpResponse(json.dumps(dict(entity)), status_code=200)
    except Exception as e:
        logging.error(f"Error updating task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("complete_task function triggered")
    try:
        task_id = req.route_params.get("id")
        table = get_table_client()
        entity = table.get_entity(partition_key="task", row_key=task_id)

        entity["status"] = "completed"
        entity["completed_at"] = datetime.utcnow().isoformat()

        table.update_entity(mode="merge", entity=entity)
        return func.HttpResponse(json.dumps(dict(entity)), status_code=200)
    except Exception as e:
        logging.error(f"Error completing task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("delete_task function triggered")
    try:
        task_id = req.route_params.get("id")
        table = get_table_client()
        table.delete_entity(partition_key="task", row_key=task_id)
        return func.HttpResponse("Task deleted", status_code=200)
    except Exception as e:
        logging.error(f"Error deleting task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="analytics/completion", methods=["GET"])
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("task_completion_stats function triggered")
    try:
        table = get_table_client()
        entities = table.query_entities("PartitionKey eq 'task'")
        tasks = [dict(e) for e in entities]
        completed = [t for t in tasks if t["status"] == "completed"]
        rate = round(len(completed) / len(tasks) * 100, 2) if tasks else 0
        return func.HttpResponse(json.dumps({"completion_rate": rate}), status_code=200)
    except Exception as e:
        logging.error(f"Error getting completion stats: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="analytics/productivity", methods=["GET"])
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("productivity_metrics function triggered")
    try:
        table = get_table_client()
        entities = table.query_entities("PartitionKey eq 'task'")
        tasks = [dict(e) for e in entities]
        created = len(tasks)
        completed_tasks = [t for t in tasks if t["status"] == "completed" and t.get("completed_at")]
        completed = len(completed_tasks)

        total_time = 0
        for task in completed_tasks:
            start = datetime.fromisoformat(task["created_at"])
            end = datetime.fromisoformat(task["completed_at"])
            total_time += (end - start).total_seconds()

        avg_time_mins = round((total_time / 60 / completed), 2) if completed else 0

        return func.HttpResponse(json.dumps({
            "tasks_created": created,
            "tasks_completed": completed,
            "completion_rate": round((completed / created) * 100, 2) if created else 0,
            "average_completion_time_minutes": avg_time_mins
        }), status_code=200)
    except Exception as e:
        logging.error(f"Error calculating productivity metrics: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)
