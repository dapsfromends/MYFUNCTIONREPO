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


