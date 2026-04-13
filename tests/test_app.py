import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as client:
        yield client


@pytest.fixture
def logged_in_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    return client


def test_update_pw_missing_fields(client):
    res = client.patch("/updatePw", json={})
    assert res.status_code == 400


def test_add_task_not_logged_in(client):
    res = client.patch("/addTask", json={
        "taskName": "Test", "taskDate": "2026-01-01", "type": "Normal"
    })

    assert res.status_code == 401
    assert b"Not logged in" in res.data


def test_settings_toggle_not_logged_in(client):
    res = client.patch("/settings/toggle",
                       json={"key": "reminders", "value": True})
    assert res.status_code == 401


def test_settings_toggle_invalid_key(logged_in_client):
    res = logged_in_client.patch(
        "/settings/toggle", json={"key": "injectedField", "value": True})
    assert b"Invalid setting" in res.data


def test_delete_task_missing_body(client):
    res = client.delete("/deleteTask", json={})
    assert res.status_code == 400


def test_update_pw_missing_fields(client):
    res = client.patch("/updatePw", json={})
    assert res.status_code == 400


def test_delete_task_missing_body(client):
    res = client.delete("/deleteTask", json={})
    assert res.status_code == 400
