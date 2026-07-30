from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: int
    name: str
    report_type: str
    generated_on: str
    status: str

    class Config:
        from_attributes = True