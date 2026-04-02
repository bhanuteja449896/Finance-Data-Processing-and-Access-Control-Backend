# Finance Data Processing and Access Control Backend

A complete backend implementation for the assignment using **FastAPI + SQLAlchemy** with SQLite (default local) and PostgreSQL-ready deployment support.

## Why this design

This implementation focuses on:
- Clear API boundaries (auth, users, records, dashboard)
- Explicit role-based access control (viewer, analyst, admin)
- Strong validation and predictable errors
- Clean data modeling with real persistence
- Test coverage for main business flows and permission checks

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy ORM
- SQLite for local development
- PostgreSQL (Neon) support for deployment
- OAuth2 password flow + bearer token (JWT)
- Pytest for API tests

## Features Implemented

### 1) User and Role Management

- Create and manage users
- Assign roles: `viewer`, `analyst`, `admin`
- Active/inactive status support
- Role-aware access control on every protected endpoint

### 2) Financial Records Management

- Create records (admin)
- View/list records (admin, analyst)
- Update records (admin)
- Delete records (admin)
- Filter records by:
	- `date_from`
	- `date_to`
	- `category`
	- `record_type` (`income` or `expense`)

### 3) Dashboard Summary APIs

`GET /dashboard/summary` returns:
- Total income
- Total expense
- Net balance
- Category-wise totals
- Recent activity
- Monthly trends

### 4) Access Control Logic

Role rules:
- `viewer`: can access dashboard summaries only
- `analyst`: can view records and dashboard summaries
- `admin`: full management of users and records + dashboard access

### 5) Validation and Error Handling

- Pydantic request validation with constraints
- Structured validation response format (`code: VALIDATION_ERROR`)
- Consistent HTTP error responses with error codes (`FORBIDDEN`, `UNAUTHORIZED`, etc.)

### 6) Data Persistence

- SQLite database (`finance.db`) created automatically on startup
- SQLAlchemy models for `User` and `FinancialRecord`
- Deployment-ready PostgreSQL support through `DATABASE_URL`

## Environment Variables

- `DATABASE_URL` (optional for local, required for deployment)
	- Local default: `sqlite:///./finance.db`
	- Neon/PostgreSQL example:
		`postgresql://<user>:<password>@<host>/<db>?sslmode=require&channel_binding=require`
- `TESTING` (used by tests): `1`

## Project Structure

```text
app/
	database.py
	dependencies.py
	main.py
	models.py
	schemas.py
	security.py
	routers/
		auth.py
		users.py
		records.py
		dashboard.py
tests/
	test_api.py
requirements.txt
pytest.ini
```

## Setup and Run

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the API:

```bash
uvicorn app.main:app --reload
```

3. Open docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Initial Bootstrap Flow

Because the system starts with no users, first create the initial admin:

```http
POST /auth/bootstrap-admin
```

Example body:

```json
{
	"username": "admin",
	"full_name": "Admin User",
	"password": "AdminPass123",
	"role": "admin",
	"is_active": true
}
```

After that, login to receive token:

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded
username=admin&password=AdminPass123
```

Use returned bearer token for protected endpoints.

## API Endpoints Summary

### System

- `GET /health` - health check

### Auth

- `POST /auth/bootstrap-admin` - create first admin user (one-time)
- `POST /auth/token` - login and get access token
- `GET /auth/me` - current authenticated user

### Users (admin only)

- `POST /users/` - create user
- `GET /users/` - list users (pagination: `skip`, `limit`)
- `GET /users/{user_id}` - get user
- `PATCH /users/{user_id}` - update user status/role/profile/password

### Records

- `POST /records/` - create record (admin)
- `GET /records/` - list records (admin, analyst)
- `GET /records/{record_id}` - get one (admin, analyst)
- `PUT /records/{record_id}` - update (admin)
- `DELETE /records/{record_id}` - delete (admin)

### Dashboard

- `GET /dashboard/summary` - summary metrics (viewer, analyst, admin)

## Run Tests

```bash
pytest
```

## Deploy on Vercel (Neon PostgreSQL)

1. Push latest code (includes `vercel.json` and `api/index.py`).
2. In Vercel: import the GitHub repo and deploy.
3. In Vercel project settings, add environment variable:
	- `DATABASE_URL` = your Neon connection string
4. Redeploy the project.
5. Open API docs at:
	- `https://<your-vercel-domain>/docs`

Notes:
- Do not hardcode database credentials in source code.
- App tables are created automatically on startup.

Tests cover:
- Bootstrap and login flow
- RBAC enforcement for viewer/analyst/admin
- Record creation/listing and permission checks
- Dashboard aggregation values
- Validation error behavior

## Assumptions and Tradeoffs

- JWT secret is hardcoded for assignment simplicity and should be env-driven in production.
- SQLite is used for easy local setup and portability.
- No refresh token flow implemented (access-token only).
- Soft delete is not enabled; delete is hard delete.

## Humanized Submission Notes

This project intentionally prioritizes:
- practical architecture over overengineering,
- explicit business rules over hidden behavior,
- clear role enforcement over implicit assumptions,
- and maintainability/readability for real team review.

It is designed to be easy to run, easy to test, and easy to evaluate.