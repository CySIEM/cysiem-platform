from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.dashboard import router as dashboard_router
from routes.alerts import router as alerts_router
from routes.threats import router as threats_router
from routes.recommendations import router as recommendations_router
from routes.reports import router as reports_router
from routes.assets import router as assets_router
from routes.investigation import router as investigation_router
from routes.copilot import router as copilot_router

app = FastAPI(
    title="CySIEM Backend",
    version="1.0.0",
    description="Backend API for CySIEM Dashboard, Response & Integration"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this later in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routes
app.include_router(dashboard_router)
app.include_router(alerts_router)
app.include_router(threats_router)
app.include_router(recommendations_router)
app.include_router(reports_router)
app.include_router(assets_router)
app.include_router(investigation_router)
app.include_router(copilot_router)


@app.get("/")
def home():
    return {
        "message": "CySIEM Backend Running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }