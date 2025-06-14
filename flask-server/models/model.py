from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    question: str
    file_url: Optional[str] = None
    access_level: str