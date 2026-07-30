from fastapi import APIRouter
from services.team1_service import Team1Service
from schemas.alert import AlertResponse

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)

team1_service = Team1Service()


@router.get("/", response_model=list[AlertResponse])
def get_alerts():
    return team1_service.get_alerts()