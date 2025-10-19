from pydantic import BaseModel, Field


class Message(BaseModel):
    id: int = Field(..., gt=0, description="Message ID must be positive")
    text: str = Field(..., min_length=1, max_length=10000, description="Message content")


