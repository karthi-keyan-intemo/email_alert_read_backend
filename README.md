# Email Alert Reader

## Project
Email Alert Reader is a Python backend for ingesting and processing email-based alert notifications. This Phase 1 focuses on the core backend foundation: project setup, PostgreSQL configuration, SQLAlchemy modeling, and Alembic migration management.

## Technology
- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic Settings

## Setup

Create a virtual environment:

```bash
python -m venv venv
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the environment file `.env` using the provided `.env.example` values.

Create the PostgreSQL database:

```sql
CREATE DATABASE email_alert_reader;
```

Run the migration:

```bash
alembic upgrade head
```

Start the application:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```
