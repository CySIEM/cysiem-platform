from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    severity: str
    title: str
    source: str
    status: str

    class Config:
        from_attributes = True