import azure.functions as func
import logging
import json
import uuid
from datetime import datetime

# Initialize the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# In-memory database for tasks (would be replaced with proper storage in production)
tasks = []




# Create a new task
@app.route(route="tasks", methods=["POST"])
def create_task(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Create Task function processed a request.')
    
    try:
        # Get request body
        req_body = req.get_json()
        
        # Log the request
        logging.info(f'Request body: {req_body}')
        
        # Check if required fields are present
        if not req_body or 'title' not in req_body:
            logging.warning('Missing required field: title')
            return func.HttpResponse(
                "Please include a title in your request",
                status_code=400
            )
            
        # Create new task with unique ID
        new_task = {
            "id": str(uuid.uuid4()),
            "title": req_body.get("title"),
            "description": req_body.get("description", ""),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        # Log task creation
        logging.info(f'Created task with ID: {new_task["id"]}, Title: "{new_task["title"]}"')
        
        # Add to our database
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

