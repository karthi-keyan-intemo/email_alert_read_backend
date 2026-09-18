from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.email_alert import router as email_alert_router
from app.api.routes.auth import router as auth_router
from app.api.routes.access import router as access_router
from app.api.routes.integrations import router as integration_router
from app.cron import create_scheduler


def _setup_app_logging() -> None:
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    logger.propagate = False


_setup_app_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application lifespan")
    scheduler = create_scheduler()
    if scheduler is not None:
        scheduler.start()
        logger.info("Application cron scheduler started")
    yield
    if scheduler is not None:
        logger.info("Shutting down application lifespan")
        scheduler.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://strong-toffee-b99918.netlify.app",
        "https://email-error-dashboard.netlify.app",
        "http://localhost:5678",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "UP"}

app.include_router(email_alert_router)
app.include_router(auth_router)
app.include_router(access_router)
app.include_router(integration_router)
