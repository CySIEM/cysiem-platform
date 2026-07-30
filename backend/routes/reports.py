from fastapi import APIRouter
from services.team4_service import Team4Service
from schemas.report import ReportResponse

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

team4_service = Team4Service()


@router.get("/", response_model=list[ReportResponse])
def get_reports():
    return team4_service.get_reports()