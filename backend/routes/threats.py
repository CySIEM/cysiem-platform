from fastapi import APIRouter
from services.team3_service import Team3Service

router = APIRouter(
    prefix="/threats",
    tags=["Threat Activity"]
)

team3_service = Team3Service()


@router.get("/")
def get_threat_activity():
    return team3_service.get_threats()