from pydantic import BaseModel


class DashboardResponse(BaseModel):
    critical: int
    high: int
    medium: int
    assets: int

    class Config:
        from_attributes = True