import json
import azure.functions as func
import pytest
from datetime import datetime, timedelta
import uuid

from function_app import (
    create_task,
    get_tasks,
    get_task_by_id,
    update_task,
    delete_task, 
    complete_task,

)


class DummyHttpRequest(func.HttpRequest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._route_params = {}

    @property
    def route_params(self):
        return self._route_params

    @route_params.setter
    def route_params(self, value):
        self._route_params = value

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
    result = json.loads(resp.get_body().decode())
    
    assert result["title"] == "New Task"
    assert result["description"] == "This is a new task"
    assert result["status"] == "pending"
    assert result["completed_at"] is None
    assert "id" in result
    assert "created_at" in result

# Test get all tasks
def test_get_tasks(populated_tasks):
    
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
    result = json.loads(resp.get_body().decode())
    assert len(result) == 2
    assert any(task["title"] == "Test Task" for task in result)
    assert any(task["title"] == "Completed Task" for task in result)

# Test get task by ID
def test_get_task_by_id(populated_tasks):
    task_id = populated_tasks[0]["id"]
    
    # Create a DummyHttpRequest with route_params support
    req = DummyHttpRequest(
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
    
    result = json.loads(resp.get_body().decode())
    assert result["id"] == task_id
    assert result["title"] == "Test Task"

# Test get task by ID - not found
def test_get_task_by_id_not_found(reset_tasks):
    non_existent_id = str(uuid.uuid4())
    
    req = DummyHttpRequest(
        method='GET',
        url=f'/api/tasks/{non_existent_id}',
        body=None,
        params={}
    )
    req.route_params = {"id": non_existent_id}
    
    resp = get_task_by_id(req)
    
    assert resp.status_code == 404
    assert "Task not found" in resp.get_body().decode()

# Test update task
def test_update_task(populated_tasks):
    task_id = populated_tasks[0]["id"]
    
    update_data = {
        "title": "Updated Task",
        "description": "This task has been updated",
        "status": "in-progress"
    }
    
    req = DummyHttpRequest(
        method='PUT',
        url=f'/api/tasks/{task_id}',
        body=json.dumps(update_data).encode(),
        params={}
    )
    req.route_params = {"id": task_id}
    
    resp = update_task(req)
    
    assert resp.status_code == 200
    result = json.loads(resp.get_body().decode())
    
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