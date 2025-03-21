import json
import azure.functions as func
import pytest
from datetime import datetime, timedelta
import uuid

# Import all functions from function_app.py
from function_app import (
     
    create_task, 
    get_tasks, 
    get_task_by_id, 
    update_task, 
    delete_task, 
    complete_task,
    task_completion_stats,
    productivity_metrics
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

# Test health check endpoint
def test_healthcheck():
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='GET',
        url='/api/healthcheck',
        body=None,
        params={}
    )
    
    # Call our function
    resp = healthcheck(req)
    
    # Check response
    assert resp.status_code == 200
    assert "TaskHub API is up and running!" in resp.get_body().decode()

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

# Test get all tasks
def test_get_tasks(populated_tasks):
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='GET',
        url='/api/tasks',
        body=None,
        params={}
    )
    
    # Call our function
    resp = get_tasks(req)
    
    # Check response
    assert resp.status_code == 200
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify we got back all tasks
    assert len(result) == 2
    assert any(task["title"] == "Test Task" for task in result)
    assert any(task["title"] == "Completed Task" for task in result)

# Test get tasks with status filter
def test_get_tasks_with_status_filter(populated_tasks):
    # Create a mock HTTP request with status parameter
    req = func.HttpRequest(
        method='GET',
        url='/api/tasks',
        body=None,
        params={"status": "completed"}
    )
    
    # Call our function
    resp = get_tasks(req)
    
    # Check response
    assert resp.status_code == 200
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify we only got completed tasks
    assert len(result) == 1
    assert result[0]["title"] == "Completed Task"
    assert result[0]["status"] == "completed"

# Test get task by ID
def test_get_task_by_id(populated_tasks):
    task_id = populated_tasks[0]["id"]
    
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='GET',
        url=f'/api/tasks/{task_id}',
        body=None,
        params={}
    )
    req.route_params = {"id": task_id}
    
    # Call our function
    resp = get_task_by_id(req)
    
    # Check response
    assert resp.status_code == 200
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify we got the right task
    assert result["id"] == task_id
    assert result["title"] == "Test Task"

# Test get task by ID - not found
def test_get_task_by_id_not_found(reset_tasks):
    # Create a mock HTTP request with a non-existent ID
    non_existent_id = str(uuid.uuid4())
    
    req = func.HttpRequest(
        method='GET',
        url=f'/api/tasks/{non_existent_id}',
        body=None,
        params={}
    )
    req.route_params = {"id": non_existent_id}
    
    # Call our function
    resp = get_task_by_id(req)
    
    # Check response
    assert resp.status_code == 404
    assert "Task not found" in resp.get_body().decode()

# Test update task
def test_update_task(populated_tasks):
    task_id = populated_tasks[0]["id"]
    
    # Create update data
    update_data = {
        "title": "Updated Task",
        "description": "This task has been updated",
        "status": "in-progress"
    }
    
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='PUT',
        url=f'/api/tasks/{task_id}',
        body=json.dumps(update_data).encode(),
        params={}
    )
    req.route_params = {"id": task_id}
    
    # Call our function
    resp = update_task(req)
    
    # Check response
    assert resp.status_code == 200
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify the task was updated correctly
    assert result["id"] == task_id
    assert result["title"] == "Updated Task"
    assert result["description"] == "This task has been updated"
    assert result["status"] == "in-progress"

# Test complete task
def test_complete_task(populated_tasks):
    task_id = populated_tasks[0]["id"]
    
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='PATCH',
        url=f'/api/tasks/{task_id}/complete',
        body=None,
        params={}
    )
    req.route_params = {"id": task_id}
    
    # Call our function
    resp = complete_task(req)
    
    # Check response
    assert resp.status_code == 200
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify the task was completed
    assert result["id"] == task_id
    assert result["status"] == "completed"
    assert result["completed_at"] is not None

# Test delete task
def test_delete_task(populated_tasks):
    task_id = populated_tasks[0]["id"]
    initial_count = len(populated_tasks)
    
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='DELETE',
        url=f'/api/tasks/{task_id}',
        body=None,
        params={}
    )
    req.route_params = {"id": task_id}
    
    # Call our function
    resp = delete_task(req)
    
    # Check response
    assert resp.status_code == 200
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify the response contains the deleted task
    assert result["message"] == "Task deleted successfully"
    assert result["task"]["id"] == task_id
    
    # Verify the task was actually removed
    import function_app
    assert len(function_app.tasks) == initial_count - 1
    assert not any(task["id"] == task_id for task in function_app.tasks)

# Test analytics - task completion stats
def test_task_completion_stats(populated_tasks):
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='GET',
        url='/api/analytics/completion',
        body=None,
        params={}
    )
    
    # Call our function
    resp = task_completion_stats(req)
    
    # Check response
    assert resp.status_code == 200
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify the statistics
    assert result["total_tasks"] == 2
    assert result["completed_tasks"] == 1
    assert result["pending_tasks"] == 1
    assert result["completion_percentage"] == 50.0

# Test analytics - productivity metrics
def test_productivity_metrics(populated_tasks):
    # Create a mock HTTP request
    req = func.HttpRequest(
        method='GET',
        url='/api/analytics/productivity',
        body=None,
        params={}
    )
    
    # Call our function
    resp = productivity_metrics(req)
    
    # Check response
    assert resp.status_code == 200
    
    # Parse the returned JSON
    result = json.loads(resp.get_body().decode())
    
    # Verify the metrics
    assert result["tasks_created"] == 2
    assert result["tasks_completed"] == 1
    assert result["completion_rate"] == 50.0
    assert "average_completion_time_hours" in result