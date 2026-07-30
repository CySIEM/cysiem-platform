from pydantic import BaseModel


class InvestigationResponse(BaseModel):
    id: int
    case_id: str
    title: str
    severity: str
    status: str
    assigned_to: str

    class Config:
        from_attributes = True