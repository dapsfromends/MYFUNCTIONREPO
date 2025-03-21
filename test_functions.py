import json
import azure.functions as func
import pytest
from datetime import datetime, timedelta
import uuid

# Import all functions from function_app.py
from function_app import (
    
    create_task, 
    
)

# Mock data setup
@pytest.fixture
def reset_tasks():
    """Reset the tasks list before each test"""
    import function_app
    function_app.tasks = []
    yield
    function_app.tasks = []

@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    task_id = str(uuid.uuid4())
    created_time = datetime.now().isoformat()
    return {
        "id": task_id,
        "title": "Test Task",
        "description": "A task created for testing",
        "status": "pending",
        "created_at": created_time,
        "completed_at": None
    }

@pytest.fixture
def populated_tasks(reset_tasks, sample_task):
    """Populate the tasks list with sample data"""
    import function_app
    
    # Add the sample task
    function_app.tasks.append(sample_task)
    
    # Add a completed task
    completed_task = {
        "id": str(uuid.uuid4()),
        "title": "Completed Task",
        "description": "A task that is already completed",
        "status": "completed",
        "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "completed_at": datetime.now().isoformat()
    }
    function_app.tasks.append(completed_task)
    
    return function_app.tasks



# Test creating a task
def test_create_task(reset_tasks):
    # Create a mock HTTP request
    task_data = {
        "title": "New Task",
        "description": "This is a new task"
    }
    
    req = func.HttpRequest(
        method='POST',
        url='/api/tasks',
        body=json.dumps(task_data).encode(),
        params={}
    )
    
    # Call our function
    resp = create_task(req)
    
    # Check response
    assert resp.status_code == 201
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify the task was created with the right attributes
    assert result["title"] == "New Task"
    assert result["description"] == "This is a new task"
    assert result["status"] == "pending"
    assert result["completed_at"] is None
    assert "id" in result
    assert "created_at" in result
