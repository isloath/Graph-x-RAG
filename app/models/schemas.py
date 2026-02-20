from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    approved = "approved"
    rejected = "rejected"
    disbursed = "disbursed"


class RiskDecision(str, Enum):
    reject = "REJECT"
    review = "REVIEW"
    approve = "APPROVE"


class ApplicationIn(BaseModel):
    application_id: str
    customer_id: str
    created_at: datetime
    phone: str | None = None
    email: str | None = None
    document_id: str | None = None
    device_id: str | None = None
    bank_account: str | None = None
    wallet_id: str | None = None
    loan_amount: float = Field(gt=0)
    status: ApplicationStatus


class ApplicationListResponse(BaseModel):
    items: list[ApplicationIn]
    page: int
    page_size: int
    total: int


class RiskBreakdown(BaseModel):
    shared_phone: int = 0
    shared_document: int = 0
    shared_device: int = 0
    high_degree_identifier: int = 0
    in_fraud_cluster: int = 0


class RiskResult(BaseModel):
    application_id: str
    score: int
    decision: RiskDecision
    breakdown: RiskBreakdown
    evidence: list[str] = Field(default_factory=list)


class IngestRequest(BaseModel):
    applications: list[ApplicationIn] = Field(default_factory=list)


class IngestResponse(BaseModel):
    ingested: int


class FraudRing(BaseModel):
    community_id: str
    size: int
    applications: list[str]


class SearchResult(BaseModel):
    id: str
    score: float
    payload: dict[str, Any]


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=5, ge=1, le=20)


class RAGResponse(BaseModel):
    question: str
    answer: str
    evidence: list[str]


class ResetResponse(BaseModel):
    status: str
