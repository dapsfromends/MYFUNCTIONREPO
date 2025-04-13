import logging
import azure.functions as func
from azure.data.tables import TableServiceClient, TableEntity
from datetime import datetime
import json
import uuid
import os

app = func.FunctionApp()

# Table Storage setup
connection_string = os.environ.get("AzureWebJobsStorage")
table_name = os.environ.get("TABLE_NAME", "TasksTable")
table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
task_table = table_service.get_table_client(table_name)

def to_task_dict(entity):
    return {
        "id": entity["RowKey"],
        "title": entity.get("title", ""),
        "description": entity.get("description", ""),
        "status": entity.get("status", "pending"),
        "created_at": entity.get("created_at"),
        "completed_at": entity.get("completed_at")
    }

@app.route(route="tasks", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("create_task function triggered")

    try:
        req_body = req.get_json()
        logging.info(f"Received payload: {req_body}")

        task_id = str(uuid.uuid4())
        entity = {
            "PartitionKey": "tasks",
            "RowKey": task_id,
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }

        task_table.create_entity(entity)
        logging.info(f"Task stored in Table Storage: {task_id}")
        return func.HttpResponse(json.dumps(to_task_dict(entity)), status_code=201)

    except Exception as e:
        logging.error(f"Exception in create_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_tasks(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_tasks function triggered")

    try:
        status_filter = req.params.get("status")
        entities = task_table.query_entities("PartitionKey eq 'tasks'")
        tasks = [to_task_dict(e) for e in entities]

        if status_filter:
            tasks = [t for t in tasks if t["status"] == status_filter]

        return func.HttpResponse(json.dumps(tasks), status_code=200)

    except Exception as e:
        logging.error(f"Exception in get_tasks: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_task_by_id(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("get_task_by_id function triggered")

    try:
        task_id = req.route_params.get("id")
        entity = task_table.get_entity(partition_key="tasks", row_key=task_id)
        return func.HttpResponse(json.dumps(to_task_dict(entity)), status_code=200)

    except Exception as e:
        logging.warning(f"Task not found: {task_id}")
        return func.HttpResponse("Task not found", status_code=404)

@app.route(route="tasks/{id}", methods=["PUT"], auth_level=func.AuthLevel.ANONYMOUS)
def update_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("update_task function triggered")

    try:
        task_id = req.route_params.get("id")
        req_body = req.get_json()
        entity = task_table.get_entity(partition_key="tasks", row_key=task_id)

        entity["title"] = req_body.get("title", entity["title"])
        entity["description"] = req_body.get("description", entity["description"])
        entity["status"] = req_body.get("status", entity["status"])

        task_table.update_entity(entity, mode="MERGE")
        return func.HttpResponse(json.dumps(to_task_dict(entity)), status_code=200)

    except Exception as e:
        logging.error(f"Exception in update_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}/complete", methods=["PATCH"], auth_level=func.AuthLevel.ANONYMOUS)
def complete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("complete_task function triggered")

    try:
        task_id = req.route_params.get("id")
        entity = task_table.get_entity(partition_key="tasks", row_key=task_id)

        entity["status"] = "completed"
        entity["completed_at"] = datetime.utcnow().isoformat()
        task_table.update_entity(entity, mode="MERGE")

        return func.HttpResponse(json.dumps(to_task_dict(entity)), status_code=200)

    except Exception as e:
        logging.error(f"Exception in complete_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="tasks/{id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def delete_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("delete_task function triggered")

    try:
        task_id = req.route_params.get("id")
        task_table.delete_entity(partition_key="tasks", row_key=task_id)
        return func.HttpResponse(json.dumps({
            "message": "Task deleted successfully",
            "task_id": task_id
        }), status_code=200)

    except Exception as e:
        logging.error(f"Exception in delete_task: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="analytics/completion", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def task_completion_stats(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("task_completion_stats function triggered")

    try:
        entities = task_table.query_entities("PartitionKey eq 'tasks'")
        tasks = [to_task_dict(e) for e in entities]

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

        return func.HttpResponse(json.dumps(stats), status_code=200)

    except Exception as e:
        logging.error(f"Exception in task_completion_stats: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)

@app.route(route="analytics/productivity", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def productivity_metrics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("productivity_metrics function triggered")

    try:
        entities = task_table.query_entities("PartitionKey eq 'tasks'")
        tasks = [to_task_dict(e) for e in entities]
        completed_tasks = [t for t in tasks if t["status"] == "completed"]

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

        return func.HttpResponse(json.dumps(metrics), status_code=200)

    except Exception as e:
        logging.error(f"Exception in productivity_metrics: {str(e)}")
        return func.HttpResponse("Internal server error", status_code=500)
