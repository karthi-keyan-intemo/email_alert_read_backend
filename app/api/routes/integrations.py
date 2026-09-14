from secrets import compare_digest

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.repositories.email_alert_repository import EmailAlertRepository
from app.schemas.n8n_integration import N8nAzureTaskWebhookRequest, N8nAzureTaskWebhookResponse
from app.services.n8n_integration_service import N8nIntegrationService

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])


@router.post(
    "/n8n/azure-task",
    response_model=N8nAzureTaskWebhookResponse,
    summary="Update Azure task references for matching alert error messages",
    description="Machine-to-machine webhook for n8n. Validates the dedicated shared secret, searches alerts using a case-insensitive error_message contains match, and updates the azure_task field for all matching records.",
)
def update_azure_task_for_matching_error_message(
    request: N8nAzureTaskWebhookRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    provided_secret = http_request.headers.get("X-Webhook-Secret")
    if not provided_secret or not provided_secret.strip() or not compare_digest(provided_secret, settings.N8N_WEBHOOK_SECRET):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    repository = EmailAlertRepository(db=db)
    service = N8nIntegrationService(repository=repository)

    try:
        alerts_updated = service.update_azure_task_for_error_message(
            error_message=request.error_message,
            azure_task_url=request.azure_task_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return N8nAzureTaskWebhookResponse(
        success=True,
        error_message=request.error_message,
        azure_task_url=request.azure_task_url,
        alerts_updated=alerts_updated,
    )
