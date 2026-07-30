from fastapi import APIRouter
from services.team5_service import Team5Service
from schemas.copilot import CopilotRequest, CopilotResponse

router = APIRouter(
    prefix="/ask",
    tags=["AI Security Copilot"]
)

team5_service = Team5Service()


@router.post("/", response_model=CopilotResponse)
def ask_copilot(request: CopilotRequest):
    return team5_service.ask_ai(request.question)