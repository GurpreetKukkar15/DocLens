from pydantic import BaseModel, field_validator
from typing import List


class QueryRequest(BaseModel):
    query: str

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class DocumentAnswer(BaseModel):
    filename: str
    answer: str
    citation: str


class UploadResponse(BaseModel):
    status: str
    filename: str
    pages: int
    chunks: int


class QueryResponse(BaseModel):
    query: str
    doc_answers: List[DocumentAnswer]
    themes: str


class DocumentListResponse(BaseModel):
    documents: List[str]
    count: int


class HealthResponse(BaseModel):
    status: str
    message: str
