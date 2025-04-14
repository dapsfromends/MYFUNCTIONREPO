import json
import os
import uuid
import pytest
from datetime import datetime

import azure.functions as func
from azure.data.tables import TableServiceClient

from function_app import (
    create_task, get_tasks, get_task_by_id,
    update_task, complete_task, delete_task,
    task_completion_stats, productivity_metrics
)

TABLE_NAME = "TasksTable"
connection_string = os.getenv("AZURE_TABLES_CONNECTION_STRING")
table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
table_client = table_service.get_table_client(table_name=TABLE_NAME)

@pytest.fixture
def reset_tasks():
    entities = table_client.query_entities("PartitionKey eq 'task'")
    for e in entities:
        if e["title"].startswith("Test"):
            table_client.delete_entity("task", e["RowKey"])
    yield
    # Post-test cleanup
    entities = table_client.query_entities("PartitionKey eq 'task'")
    for e in entities:
        if e["title"].startswith("Test"):
            table_client.delete_entity("task", e["RowKey"])

@pytest.fixture
def populated_tasks(reset_tasks):
    task_1 = {
        "PartitionKey": "task",
        "RowKey": str(uuid.uuid4()),
        "title": "Test Task 1",
        "description": "A task created for testing",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None
    }
    task_2 = {
        "PartitionKey": "task",
        "RowKey": str(uuid.uuid4()),
        "title": "Test Task 2",
        "description": "A task that is already completed",
        "status": "completed",
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat()
    }
    table_client.create_entity(entity=task_1)
    table_client.create_entity(entity=task_2)
    return [task_1, task_2]

def test_create_task(reset_tasks):
    task_data = {
        "title": "Test New Task",
        "description": "This is a test"
    }
    req = func.HttpRequest(
        method='POST',
        url='/api/tasks',
        body=json.dumps(task_data).encode(),
        params={}
    )
    resp = create_task(req)
    assert resp.status_code == 201

def test_get_tasks(populated_tasks):
    req = func.HttpRequest(method='GET', url='/api/tasks', body=None, params={})
    resp = get_tasks(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert isinstance(data, list)
    assert len(data) >= 2

def test_get_tasks_with_status_filter(populated_tasks):
    req = func.HttpRequest(method='GET', url='/api/tasks', body=None, params={"status": "completed"})
    resp = get_tasks(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert all(task["status"] == "completed" for task in data)

def test_get_task_by_id(populated_tasks):
    task_id = populated_tasks[0]["RowKey"]
    req = func.HttpRequest(method='GET', url=f'/api/tasks/{task_id}', body=None, params={})
    req.route_params = {"id": task_id}
    resp = get_task_by_id(req)
    assert resp.status_code == 200
    task = json.loads(resp.get_body())
    assert task["id"] == task_id

def test_get_task_by_id_not_found():
    req = func.HttpRequest(method='GET', url='/api/tasks/fake-id', body=None, params={})
    req.route_params = {"id": "fake-id"}
    resp = get_task_by_id(req)
    assert resp.status_code == 404

def test_update_task(populated_tasks):
    task_id = populated_tasks[0]["RowKey"]
    update_data = {
        "title": "Test Updated Task",
        "description": "Updated description",
        "status": "in-progress"
    }
    req = func.HttpRequest(
        method='PUT',
        url=f'/api/tasks/{task_id}',
        body=json.dumps(update_data).encode(),
        params={}
    )
    req.route_params = {"id": task_id}
    resp = update_task(req)
    assert resp.status_code == 200
    updated = json.loads(resp.get_body())
    assert updated["title"] == "Test Updated Task"

def test_complete_task(populated_tasks):
    task_id = populated_tasks[0]["RowKey"]
    req = func.HttpRequest(method='PATCH', url=f'/api/tasks/{task_id}/complete', body=None, params={})
    req.route_params = {"id": task_id}
    resp = complete_task(req)
    assert resp.status_code == 200
    task = json.loads(resp.get_body())
    assert task["status"] == "completed"

def test_delete_task(populated_tasks):
    task_id = populated_tasks[0]["RowKey"]
    req = func.HttpRequest(method='DELETE', url=f'/api/tasks/{task_id}', body=None, params={})
    req.route_params = {"id": task_id}
    resp = delete_task(req)
    assert resp.status_code == 200

def test_task_completion_stats(populated_tasks):
    req = func.HttpRequest(method='GET', url='/api/analytics/completion', body=None, params={})
    resp = task_completion_stats(req)
    assert resp.status_code == 200
    result = json.loads(resp.get_body())
    assert "tasks_completed_today" in result

def test_productivity_metrics(populated_tasks):
    req = func.HttpRequest(method='GET', url='/api/analytics/productivity', body=None, params={})
    resp = productivity_metrics(req)
    assert resp.status_code == 200
    result = json.loads(resp.get_body())
    assert "tasks_created" in result
    assert "tasks_completed" in result
    assert "completion_rate" in result
    assert "average_completion_time_minutes" in result
