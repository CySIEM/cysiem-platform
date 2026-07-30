from fastapi import APIRouter
from services.team4_service import Team4Service
from schemas.investigation import InvestigationResponse

router = APIRouter(
    prefix="/investigation",
    tags=["Investigation"]
)

team4_service = Team4Service()


@router.get("/", response_model=list[InvestigationResponse])
def get_investigations():
    return team4_service.get_investigations()