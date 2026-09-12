from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.email_alert import router as email_alert_router
from app.api.routes.auth import router as auth_router
from app.api.routes.access import router as access_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://strong-toffee-b99918.netlify.app",
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
