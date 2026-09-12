from datetime import date
from io import BytesIO
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.repositories.email_alert_repository import EmailAlertFilters, EmailAlertRepository
from app.services.email_alert_service import EmailAlertService
from app.services.email_reader import EmailReader

from app.db.database import get_db
from app.core.auth import require_permission
from app.models.auth import User
from app.schemas.email_alert import (
    EmailAlertAzureTaskUpdateRequest,
    EmailAlertAzureTaskUpdateResponse,
    EmailAlertReadRequest,
    EmailAlertReadResponse,
    EmailAlertResponse,
    PaginatedEmailAlertResponse,
    AnalyticsResponse,
)


router = APIRouter(
    prefix="/api/email-alerts",
    tags=["Email Alerts"],
)


@router.post(
    "/read",
    response_model=EmailAlertReadResponse,
)
def read_email_alerts(
    request: EmailAlertReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ALERT_SYNC")),
):
    email_reader = EmailReader()

    repository = EmailAlertRepository(
        db=db,
    )

    service = EmailAlertService(
        email_reader=email_reader,
        repository=repository,
    )

    result = service.process_emails(
        from_date=request.from_date,
        to_date=request.to_date,
    )

    return result


@router.get(
    "",
    response_model=PaginatedEmailAlertResponse,
)
def get_email_alerts(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    source_name: str | None = Query(default=None),
    error_type: Literal["UNKNOWN", "RESPONSE_VALIDATION"] | None = Query(default=None),
    email_subject: str | None = Query(default=None),
    error_message: str | None = Query(default=None),
    azure_task: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    alert_timestamp_from: date | None = Query(default=None),
    alert_timestamp_to: date | None = Query(default=None),
    email_received_at_from: date | None = Query(default=None),
    email_received_at_to: date | None = Query(default=None),
    sort_by: Literal["alert_timestamp", "email_received_at", "environment", "source_name", "error_type", "created_at"] = Query(default="alert_timestamp"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ALERT_VIEW")),
):
    if from_date is not None and to_date is not None and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date cannot be later than to_date")

    repository = EmailAlertRepository(
        db=db,
    )

    email_reader = EmailReader()

    service = EmailAlertService(
        email_reader=email_reader,
        repository=repository,
    )

    filters = EmailAlertFilters(
        from_date=from_date,
        to_date=to_date,
        search=search,
        environment=environment, source_name=source_name, error_type=error_type,
        email_subject=email_subject, error_message=error_message, azure_task=azure_task,
        request_id=request_id, alert_timestamp_from=alert_timestamp_from,
        alert_timestamp_to=alert_timestamp_to, email_received_at_from=email_received_at_from,
        email_received_at_to=email_received_at_to,
    )
    return service.get_email_alerts(from_date=from_date, to_date=to_date, page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order, filters=filters)


@router.get("/analytics", response_model=AnalyticsResponse)
def get_email_alert_analytics(
    from_date: date | None = Query(default=None), to_date: date | None = Query(default=None),
    environment: str | None = Query(default=None), source_name: str | None = Query(default=None),
    error_type: Literal["UNKNOWN", "RESPONSE_VALIDATION"] | None = Query(default=None),
    error_message: str | None = Query(default=None), azure_task: str | None = Query(default=None),
    db: Session = Depends(get_db), current_user: User = Depends(require_permission("ALERT_VIEW")),
):
    if from_date is not None and to_date is not None and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date cannot be later than to_date")
    filters = EmailAlertFilters(from_date=from_date, to_date=to_date, environment=environment, source_name=source_name, error_type=error_type, error_message=error_message, azure_task=azure_task)
    service = EmailAlertService(email_reader=EmailReader(), repository=EmailAlertRepository(db=db))
    return service.get_analytics(filters)


@router.get("/export")
def export_email_alerts(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ALERT_EXPORT")),
):
    if from_date is not None and to_date is not None and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date cannot be later than to_date")

    service = EmailAlertService(email_reader=EmailReader(), repository=EmailAlertRepository(db=db))
    alerts = service.export_email_alerts(from_date=from_date, to_date=to_date)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Email Alerts"
    worksheet.append([
        "Alert ID", "Environment", "Source Name", "Error Message", "Azure Task", "Request IDs",
    ])
    for alert in alerts:
        worksheet.append([
            str(alert.id), alert.environment, alert.source_name, alert.error_message, alert.azure_task,
            ", ".join(str(request.request_id) for request in alert.requests),
        ])

    output = BytesIO()
    workbook.save(output)
    filename_from = from_date.isoformat() if from_date else "all"
    filename_to = to_date.isoformat() if to_date else "all"
    headers = {"Content-Disposition": f'attachment; filename="email_alerts_{filename_from}_to_{filename_to}.xlsx"'}
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.patch(
    "/{alert_id}/azure-task",
    response_model=EmailAlertAzureTaskUpdateResponse,
)
def update_email_alert_azure_task(
    alert_id: UUID,
    request: EmailAlertAzureTaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("ALERT_EDIT")),
):
    repository = EmailAlertRepository(db=db)
    email_reader = EmailReader()
    service = EmailAlertService(
        email_reader=email_reader,
        repository=repository,
    )

    try:
        updated_alert = service.update_azure_task(
            alert_id=alert_id,
            azure_task=request.azure_task,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "id": updated_alert.id,
        "azure_task": updated_alert.azure_task,
    }