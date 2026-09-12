from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.repositories.email_alert_repository import EmailAlertRepository
from app.services.email_alert_service import EmailAlertService
from app.services.email_reader import EmailReader

from app.db.database import get_db
from app.schemas.email_alert import (
    EmailAlertAzureTaskUpdateRequest,
    EmailAlertAzureTaskUpdateResponse,
    EmailAlertReadRequest,
    EmailAlertReadResponse,
    EmailAlertResponse,
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
    response_model=list[EmailAlertResponse],
)
def get_email_alerts(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    repository = EmailAlertRepository(
        db=db,
    )

    email_reader = EmailReader()

    service = EmailAlertService(
        email_reader=email_reader,
        repository=repository,
    )

    return service.get_email_alerts(
        from_date=from_date,
        to_date=to_date,
    )


@router.patch(
    "/{alert_id}/azure-task",
    response_model=EmailAlertAzureTaskUpdateResponse,
)
def update_email_alert_azure_task(
    alert_id: UUID,
    request: EmailAlertAzureTaskUpdateRequest,
    db: Session = Depends(get_db),
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