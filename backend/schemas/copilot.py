from pydantic import BaseModel


class CopilotRequest(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    success: bool
    question: str
    answer: str

    class Config:
        from_attributes = True