from fastapi import APIRouter
from services.team3_service import Team3Service

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)

team3_service = Team3Service()


@router.get("/")
def get_recommendations():
    return team3_service.get_recommendations()