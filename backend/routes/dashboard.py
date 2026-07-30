from fastapi import APIRouter
from services.team1_service import Team1Service
from schemas.dashboard import DashboardResponse

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

team1_service = Team1Service()


@router.get("/", response_model=DashboardResponse)
def get_dashboard():
    return team1_service.get_dashboard_stats()