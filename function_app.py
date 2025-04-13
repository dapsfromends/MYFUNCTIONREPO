import os
import json
import uuid
import logging
from datetime import datetime
import azure.functions as func
from azure.data.tables import TableServiceClient, TableEntity

app = func.FunctionApp()

# Helper function to connect to the Azure Table
def get_table_client():
    connection_string = os.getenv("AZURE_TABLES_CONNECTION_STRING")
    table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
    return table_service.get_table_client("TasksTable")


@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("create_task function triggered")

    try:
        req_body = req.get_json()
        logging.info(f"Received payload: {req_body}")

        task_id = str(uuid.uuid4())
        new_task = {
            "PartitionKey": "TaskPartition",
            "RowKey": task_id,
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }

        table_client = get_table_client()
        table_client.create_entity(entity=new_task)
        logging.info(f"Task created successfully: {task_id}")

        response_body = {
            "id": task_id,
            "title": new_task["title"],
            "description": new_task["description"],
            "status": new_task["status"],
            "created_at": new_task["created_at"],
            "completed_at": new_task["completed_at"]
        }

        return func.HttpResponse(json.dumps(response_body), status_code=201)

    except Exception as e:
        logging.error(f"Exception in create_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)


@app.route(route="tasks", methods=["GET"])
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_tasks function triggered")

    try:
        table_client = get_table_client()
        status_filter = req.params.get("status")
        logging.info(f"Filter status: {status_filter}")

        if status_filter:
            entities = table_client.query_entities(f"status eq '{status_filter}'")
        else:
            entities = table_client.list_entities()

        tasks = []
        for entity in entities:
            tasks.append({
                "id": entity["RowKey"],
                "title": entity.get("title", ""),
                "description": entity.get("description", ""),
                "status": entity.get("status", ""),
                "created_at": entity.get("created_at"),
                "completed_at": entity.get("completed_at")
            })

        logging.info(f"{len(tasks)} tasks returned")
        return func.HttpResponse(json.dumps(tasks), status_code=200)

    except Exception as e:
        logging.error(f"Exception in get_tasks: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)


@app.route(route="tasks/{id}", methods=["GET"])
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_task_by_id function triggered")

    task_id = req.route_params.get("id")
    logging.info(f"Looking for task with ID: {task_id}")

    try:
        table_client = get_table_client()
        entity = table_client.get_entity(partition_key="TaskPartition", row_key=task_id)

        task = {
            "id": entity["RowKey"],
            "title": entity["title"],
            "description": entity.get("description", ""),
            "status": entity.get("status", ""),
            "created_at": entity.get("created_at"),
            "completed_at": entity.get("completed_at")
        }

        return func.HttpResponse(json.dumps(task), status_code=200)

    except Exception as e:
        logging.error(f"Task not found or error occurred: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)


@app.route(route="tasks/{id}", methods=["PUT"])
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("update_task function triggered")

    task_id = req.route_params.get("id")
    logging.info(f"Updating task ID: {task_id}")

    try:
        req_body = req.get_json()
        table_client = get_table_client()
        entity = table_client.get_entity(partition_key="TaskPartition", row_key=task_id)

        entity["title"] = req_body.get("title", entity["title"])
        entity["description"] = req_body.get("description", entity.get("description", ""))
        entity["status"] = req_body.get("status", entity.get("status", ""))

        table_client.update_entity(entity=entity, mode="Merge")

        updated_task = {
            "id": entity["RowKey"],
            "title": entity["title"],
            "description": entity["description"],
            "status": entity["status"],
            "created_at": entity["created_at"],
            "completed_at": entity["completed_at"]
        }

        return func.HttpResponse(json.dumps(updated_task), status_code=200)

    except Exception as e:
        logging.error(f"Error updating task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)


@app.route(route="tasks/{id}/complete", methods=["PATCH"])
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("complete_task function triggered")

    task_id = req.route_params.get("id")
    try:
        table_client = get_table_client()
        entity = table_client.get_entity(partition_key="TaskPartition", row_key=task_id)

        entity["status"] = "completed"
        entity["completed_at"] = datetime.utcnow().isoformat()

        table_client.update_entity(entity=entity, mode="Merge")

        completed_task = {
            "id": entity["RowKey"],
            "title": entity["title"],
            "description": entity["description"],
            "status": entity["status"],
            "created_at": entity["created_at"],
            "completed_at": entity["completed_at"]
        }

        return func.HttpResponse(json.dumps(completed_task), status_code=200)

    except Exception as e:
        logging.error(f"Error completing task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)


@app.route(route="tasks/{id}", methods=["DELETE"])
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("delete_task function triggered")

    task_id = req.route_params.get("id")
    try:
        table_client = get_table_client()
        table_client.delete_entity(partition_key="TaskPartition", row_key=task_id)

        logging.info(f"Task deleted: {task_id}")
        return func.HttpResponse("Task deleted", status_code=200)

    except Exception as e:
        logging.error(f"Error deleting task: {str(e)}")
        return func.HttpResponse("Task not found", status_code=404)


@app.route(route="analytics/completion", methods=["GET"])
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("task_completion_stats function triggered")

    try:
        table_client = get_table_client()
        all_tasks = table_client.list_entities()
        tasks = list(all_tasks)

        completed = [t for t in tasks if t.get("status") == "completed"]
        pending = [t for t in tasks if t.get("status") != "completed"]

        stats = {
            "completed_tasks": len(completed),
            "pending_tasks": len(pending),
            "total_tasks": len(tasks)
        }

        return func.HttpResponse(json.dumps(stats), status_code=200)

    except Exception as e:
        logging.error(f"Error getting completion stats: {str(e)}")
        return func.HttpResponse("Error getting stats", status_code=500)


@app.route(route="analytics/productivity", methods=["GET"])
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("productivity_metrics function triggered")

    try:
        table_client = get_table_client()
        all_tasks = list(table_client.list_entities())
        completed = [t for t in all_tasks if t.get("status") == "completed"]

        total = len(all_tasks)
        completed_count = len(completed)

        avg_time = None
        if completed_count > 0:
            durations = []
            for t in completed:
                if t.get("created_at") and t.get("completed_at"):
                    created = datetime.fromisoformat(t["created_at"])
                    completed = datetime.fromisoformat(t["completed_at"])
                    durations.append((completed - created).total_seconds() / 60)
            avg_time = sum(durations) / len(durations)

        metrics = {
            "tasks_created": total,
            "tasks_completed": completed_count,
            "completion_rate": round((completed_count / total) * 100, 2) if total > 0 else 0,
            "average_completion_time_minutes": round(avg_time, 2) if avg_time else None
        }

        return func.HttpResponse(json.dumps(metrics), status_code=200)

    except Exception as e:
        logging.error(f"Error calculating productivity metrics: {str(e)}")
        return func.HttpResponse("Error getting metrics", status_code=500)
