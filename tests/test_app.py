import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as client:
        yield client


# Test 1: Home page redirects to login
def test_home_redirects_to_login(client):
    res = client.get("/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


# Test 2: Login page loads
def test_login_page_loads(client):
    res = client.get("/login")
    assert res.status_code == 200


# Test 3: Login with missing fields
def test_login_missing_fields(client):
    res = client.post("/login", data={"username": "", "password": ""})
    assert b"All fields are required" in res.data


# Test 4: updatePw with missing fields returns 400
def test_update_pw_missing_fields(client):
    res = client.patch("/updatePw", json={})
    assert res.status_code == 400


# Test 5: addTask without being logged in
def test_add_task_not_logged_in(client):
    res = client.patch("/addTask", json={
        "taskName": "Test", "taskDate": "2026-01-01", "type": "Normal"
    })

    assert res.status_code == 401
    assert b"Not logged in" in res.data
