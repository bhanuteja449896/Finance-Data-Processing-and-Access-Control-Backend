import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["TESTING"] = "1"

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "test_finance.db"
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def bootstrap_admin(client: TestClient) -> None:
    response = client.post(
        "/auth/bootstrap-admin",
        json={
            "username": "admin",
            "full_name": "Admin User",
            "password": "AdminPass123",
            "role": "admin",
            "is_active": True,
        },
    )
    assert response.status_code == 201


def create_token(client: TestClient, username: str, password: str) -> str:
    response = client.post("/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_bootstrap_admin_can_login(client: TestClient):
    bootstrap_admin(client)
    token = create_token(client, "admin", "AdminPass123")
    me = client.get("/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["role"] == "admin"


def test_rbac_and_records_flow(client: TestClient):
    bootstrap_admin(client)
    admin_token = create_token(client, "admin", "AdminPass123")

    create_analyst = client.post(
        "/users/",
        headers=auth_headers(admin_token),
        json={
            "username": "analyst1",
            "full_name": "Analyst One",
            "password": "AnalystPass123",
            "role": "analyst",
            "is_active": True,
        },
    )
    assert create_analyst.status_code == 201

    create_viewer = client.post(
        "/users/",
        headers=auth_headers(admin_token),
        json={
            "username": "viewer1",
            "full_name": "Viewer One",
            "password": "ViewerPass123",
            "role": "viewer",
            "is_active": True,
        },
    )
    assert create_viewer.status_code == 201

    record = client.post(
        "/records/",
        headers=auth_headers(admin_token),
        json={
            "amount": 5000.0,
            "record_type": "income",
            "category": "salary",
            "date": str(date.today()),
            "notes": "Monthly salary",
        },
    )
    assert record.status_code == 201

    analyst_token = create_token(client, "analyst1", "AnalystPass123")
    list_records = client.get("/records/", headers=auth_headers(analyst_token))
    assert list_records.status_code == 200
    assert len(list_records.json()) == 1

    analyst_delete = client.delete("/records/1", headers=auth_headers(analyst_token))
    assert analyst_delete.status_code == 403

    viewer_token = create_token(client, "viewer1", "ViewerPass123")
    viewer_create = client.post(
        "/records/",
        headers=auth_headers(viewer_token),
        json={
            "amount": 100,
            "record_type": "expense",
            "category": "food",
            "date": str(date.today()),
        },
    )
    assert viewer_create.status_code == 403


def test_dashboard_summary(client: TestClient):
    bootstrap_admin(client)
    admin_token = create_token(client, "admin", "AdminPass123")

    records = [
        {"amount": 3000, "record_type": "income", "category": "Salary", "date": "2026-03-10", "notes": "Salary"},
        {"amount": 500, "record_type": "expense", "category": "Food", "date": "2026-03-11", "notes": "Groceries"},
        {"amount": 700, "record_type": "expense", "category": "Rent", "date": "2026-03-12", "notes": "Rent"},
    ]

    for payload in records:
        response = client.post("/records/", headers=auth_headers(admin_token), json=payload)
        assert response.status_code == 201

    summary = client.get("/dashboard/summary", headers=auth_headers(admin_token))
    assert summary.status_code == 200
    body = summary.json()
    assert body["total_income"] == 3000
    assert body["total_expense"] == 1200
    assert body["net_balance"] == 1800
    assert len(body["category_totals"]) >= 2


def test_validation_errors(client: TestClient):
    bootstrap_admin(client)
    admin_token = create_token(client, "admin", "AdminPass123")

    invalid = client.post(
        "/records/",
        headers=auth_headers(admin_token),
        json={
            "amount": -5,
            "record_type": "income",
            "category": "x",
            "date": "not-a-date",
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "VALIDATION_ERROR"
