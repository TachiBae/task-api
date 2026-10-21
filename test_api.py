import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def fresh_state():
    main.reset_state()


def test_list_returns_three_seed_tasks():
    r = client.get("/tasks")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_get_unknown_task_is_404():
    r = client.get("/tasks/99")
    assert r.status_code == 404
    assert "error" in r.json()


def test_create_returns_201_and_appears_in_list():
    r = client.post("/tasks", json={"title": "Buy milk"})
    assert r.status_code == 201
    assert r.json()["done"] is False
    assert len(client.get("/tasks").json()) == 4


@pytest.mark.parametrize("body", [{}, {"title": ""}, {"title": "   "}])
def test_create_with_bad_title_is_400(body):
    assert client.post("/tasks", json=body).status_code == 400


def test_update_marks_done():
    r = client.put("/tasks/2", json={"done": True})
    assert r.status_code == 200
    assert r.json()["done"] is True


def test_update_empty_body_is_400_and_unknown_is_404():
    assert client.put("/tasks/2", json={}).status_code == 400
    assert client.put("/tasks/99", json={"done": True}).status_code == 404


def test_delete_is_204_then_404():
    assert client.delete("/tasks/1").status_code == 204
    assert client.delete("/tasks/1").status_code == 404
