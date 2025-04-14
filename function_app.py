import logging
import azure.functions as func
from datetime import datetime
from azure.data.tables import TableServiceClient, TableEntity
import os
import json
import uuid

app = func.FunctionApp()
TABLE_NAME = "TasksTable"

def get_table_client():
    connection_string = os.getenv("AZURE_TABLES_CONNECTION_STRING", "UseDevelopmentStorage=true")
    table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
    return table_service.get_table_client(table_name=TABLE_NAME)

# ---------------------- TASK CRUD ---------------------- #

@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("create_task function triggered")

    try:
        req_body = req.get_json()
        logging.info(f"Received payload: {req_body}")

        new_task = {
            "PartitionKey": "tasks",
            "RowKey": str(uuid.uuid4()),
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }

        table_client = get_table_client()
        table_client.create_entity(entity=new_task)

        logging.info(f"Task created: {new_task['RowKey']}")
        return func.HttpResponse(json.dumps(new_task), status_code=201)

    except Exception as e:
        logging.error(f"Exception in create_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_tasks function triggered")
    try:
        status_filter = req.params.get("status")
        table_client = get_table_client()
        entities = list(table_client.list_entities())

        if status_filter:
            filtered = [dict(e) for e in entities if e.get("status") == status_filter]
            return func.HttpResponse(json.dumps(filtered), status_code=200)
        else:
            return func.HttpResponse(json.dumps([dict(e) for e in entities]), status_code=200)

    except Exception as e:
        logging.error(f"Exception in get_tasks: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_task_by_id triggered")
    task_id = req.route_params.get("id")

    try:
        table_client = get_table_client()
        entity = table_client.get_entity(partition_key="tasks", row_key=task_id)
        return func.HttpResponse(json.dumps(dict(entity)), status_code=200)

    except Exception as e:
        logging.error(f"Task not found or error: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("update_task triggered")
    task_id = req.route_params.get("id")

    try:
        table_client = get_table_client()
        entity = table_client.get_entity(partition_key="tasks", row_key=task_id)

        req_body = req.get_json()
        entity["title"] = req_body.get("title", entity["title"])
        entity["description"] = req_body.get("description", entity["description"])
        entity["status"] = req_body.get("status", entity["status"])

        table_client.update_entity(mode="MERGE", entity=entity)
        return func.HttpResponse(json.dumps(dict(entity)), status_code=200)

    except Exception as e:
        logging.error(f"Error updating task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("complete_task triggered")
    task_id = req.route_params.get("id")

    try:
        table_client = get_table_client()
        entity = table_client.get_entity(partition_key="tasks", row_key=task_id)
        entity["status"] = "completed"
        entity["completed_at"] = datetime.utcnow().isoformat()

        table_client.update_entity(mode="MERGE", entity=entity)
        return func.HttpResponse(json.dumps(dict(entity)), status_code=200)

    except Exception as e:
        logging.error(f"Error completing task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("delete_task triggered")
    task_id = req.route_params.get("id")

    try:
        table_client = get_table_client()
        table_client.delete_entity(partition_key="tasks", row_key=task_id)
        return func.HttpResponse("Task deleted", status_code=200)

    except Exception as e:
        logging.error(f"Error deleting task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)

# ---------------------- ANALYTICS ---------------------- #

@app.route(route="analytics/completion", methods=["GET"])
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    try:
        table_client = get_table_client()
        entities = list(table_client.list_entities())
        total = len(entities)
        completed = len([t for t in entities if t.get("status") == "completed"])
        pending = total - completed
        completion_rate = (completed / total * 100) if total > 0 else 0

        result = {
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "completion_rate": round(completion_rate, 2)
        }

        return func.HttpResponse(json.dumps(result), status_code=200)

    except Exception as e:
        logging.error(f"Error getting completion stats: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="analytics/productivity", methods=["GET"])
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    try:
        table_client = get_table_client()
        entities = list(table_client.list_entities())

        now = datetime.utcnow()
        completed = [t for t in entities if t.get("status") == "completed"]
        completed_today = [
            t for t in completed
            if "completed_at" in t and datetime.fromisoformat(t["completed_at"]).date() == now.date()
        ]
        durations = [
            (datetime.fromisoformat(t["completed_at"]) - datetime.fromisoformat(t["created_at"])).total_seconds()
            for t in completed if "completed_at" in t and "created_at" in t
        ]

        result = {
            "tasks_created": len(entities),
            "tasks_completed": len(completed),
            "tasks_completed_today": len(completed_today),
            "completion_rate": round((len(completed) / len(entities)) * 100, 2) if entities else 0,
            "average_completion_time_minutes": round(sum(durations) / 60 / len(durations), 2) if durations else 0
        }

        return func.HttpResponse(json.dumps(result), status_code=200)

    except Exception as e:
        logging.error(f"Error calculating productivity metrics: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)
