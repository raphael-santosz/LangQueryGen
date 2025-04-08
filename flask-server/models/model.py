from pydantic import BaseModel
from typing import List, Any

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    raw_query: str
    fixed_query: str
    result: List[Any]
