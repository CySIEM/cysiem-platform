from fastapi import APIRouter
from services.team2_service import Team2Service
from schemas.asset import AssetResponse

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)

team2_service = Team2Service()


@router.get("/", response_model=list[AssetResponse])
def get_assets():
    return team2_service.get_assets()