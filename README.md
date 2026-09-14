# Email Alert Reader

## Project
Email Alert Reader is a Python backend and React dashboard for ingesting and processing email-based alert notifications.

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

Configure the environment file `.env` using the provided `.env.example` values. Set `JWT_SECRET_KEY` to a long random value and never commit the real `.env` file.

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

## Authentication and Authorization

Run the auth migration after installing dependencies:

```bash
alembic upgrade head
```

Create the first administrator interactively:

```bash
python -m app.cli create-admin
```

The command normalizes the email, hashes the password, and assigns the `ADMIN` role. It does not create a duplicate user.

Login:

```text
POST /api/auth/login
{
	"email": "admin@example.com",
	"password": "your-password"
}
```

Use the returned bearer token with protected APIs. `GET /api/auth/me` returns the authenticated user. The roles are `ADMIN`, `USER`, and `VIEWER`; permissions are `ALERT_VIEW`, `ALERT_SYNC`, `ALERT_EXPORT`, and `ALERT_EDIT`.

| Role | View | Sync | Export | Edit Azure Task |
| --- | --- | --- | --- | --- |
| ADMIN | Yes | Yes | Yes | Yes |
| USER | Yes | Yes | Yes | Yes |
| VIEWER | Yes | No | No | No |

The alert endpoints require `ALERT_VIEW` for `GET /api/email-alerts`, `ALERT_SYNC` for `POST /api/email-alerts/read`, `ALERT_EXPORT` for `GET /api/email-alerts/export`, and `ALERT_EDIT` for the Azure Task PATCH endpoint.

Access management endpoints require `ACCESS_MANAGE`:

- `GET/POST/PATCH/DELETE /api/users`
- `POST /api/users/{user_id}/reset-password`
- `GET/POST/PATCH/DELETE /api/roles`
- `GET/POST/PATCH/DELETE /api/permissions`

User deletion deactivates the account. The API prevents duplicate emails and names, invalid role or permission assignments, self-deactivation, deletion of assigned roles or permissions, and removal of the last active ADMIN.

## Email Alert API

### Get alerts

`GET /api/email-alerts` returns one database-paginated page. The selected dates are inclusive; internally the end date uses the next day's midnight as an exclusive boundary.

Query parameters:

- `from_date` and `to_date`: optional `YYYY-MM-DD` values
- `page`: optional page number starting at `1` (default `1`)
- `page_size`: optional page size from `1` to `100` (default `20`)
- `search`: optional alert text search
- `sort_by`: `alert_timestamp`, `email_received_at`, `environment`, `source_name`, `error_type`, or `created_at`
- `sort_order`: `asc` or `desc`

Example:

```text
GET /api/email-alerts?from_date=2026-09-08&to_date=2026-09-12&page=1&page_size=20&search=ONEY&sort_by=alert_timestamp&sort_order=desc
```

The response includes `items`, `page`, `page_size`, `total`, `total_pages`, and a `summary` for the complete filtered range:

```json
{
	"items": [],
	"page": 1,
	"page_size": 20,
	"total": 47,
	"total_pages": 3,
	"summary": {
		"total_alerts": 47,
		"unknown_errors": 30,
		"response_validation_errors": 17,
		"total_requests": 86
	}
}
```

### Export alerts

`GET /api/email-alerts/export?from_date=2026-09-08&to_date=2026-09-10` downloads all matching alerts as an Excel `.xlsx` workbook. Export is independent of table pagination and includes one row per grouped alert with all request IDs in one cell.

### Sync alerts

`POST /api/email-alerts/read` keeps the existing Sync Now behavior. Send `from_date` and `to_date` as `YYYY-MM-DD` values in the JSON body.

The backend performs date filtering, case-insensitive search across source, environment, subject, error message, and request ID, controlled sorting, and pagination in PostgreSQL. Summary values cover the complete filtered result, not only the current page.

Column filters are sent directly to `GET /api/email-alerts`, for example:

```text
GET /api/email-alerts?page=1&page_size=20&environment=PRODUCTION&source_name=ONEY&error_type=UNKNOWN&error_message=timeout&sort_by=alert_timestamp&sort_order=desc
```

The dashboard applies filters in the table headers and no longer performs the main search or sort operation in React.

### Analytics

`GET /api/email-alerts/analytics` requires `ALERT_VIEW` and returns PostgreSQL-aggregated KPIs, daily trend data, error distribution, source analysis, environment analysis, top recurring errors, source/error-type data, and recent alerts.

Example:

```text
GET /api/email-alerts/analytics?from_date=2026-09-08&to_date=2026-09-12&environment=PRODUCTION&source_name=ONEY
```

### n8n Azure Task webhook

`POST /api/integrations/n8n/azure-task` is a dedicated machine-to-machine endpoint for n8n. It validates `X-Webhook-Secret`, checks the request body, finds every `EmailAlert` whose `error_message` contains the supplied value using a case-insensitive PostgreSQL `ILIKE` match, and updates only the `azure_task` field for all matching records.

Headers:

```text
Content-Type: application/json
X-Webhook-Secret: <secret>
```

Body:

```json
{
  "error_message": "ElementMissingInPage",
  "azure_task_url": "https://dev.azure.com/company/project/_workitems/edit/12345"
}
```

Successful response:

```json
{
  "success": true,
  "error_message": "ElementMissingInPage",
  "azure_task_url": "https://dev.azure.com/company/project/_workitems/edit/12345",
  "alerts_updated": 3
}
```

If the secret is missing, empty, or invalid, the API returns `401 Unauthorized`. If no alerts match the supplied error message, it returns `404 Not Found`.
```
