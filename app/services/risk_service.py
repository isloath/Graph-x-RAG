from __future__ import annotations

from app.models.schemas import RiskBreakdown, RiskDecision, RiskResult


class RiskService:
    async def score(
        self,
        application_id: str,
        phone_degree: int,
        document_degree: int,
        device_degree: int,
        max_identifier_degree: int,
        community_size: int,
    ) -> RiskResult:
        breakdown = RiskBreakdown()
        evidence: list[str] = []

        if phone_degree >= 2:
            breakdown.shared_phone = 20
            evidence.append(f"Phone shared by {phone_degree} applications")

        if document_degree >= 2:
            breakdown.shared_document = 40
            evidence.append(f"Document shared by {document_degree} applications")

        if device_degree >= 3:
            breakdown.shared_device = 25
            evidence.append(f"Device shared by {device_degree} applications")

        if max_identifier_degree >= 5:
            breakdown.high_degree_identifier = 30
            evidence.append(f"High-degree identifier found (degree={max_identifier_degree})")

        if community_size >= 5:
            breakdown.in_fraud_cluster = 35
            evidence.append(f"Belongs to Louvain community of size {community_size}")

        score = sum(breakdown.model_dump().values())
        if score >= 70:
            decision = RiskDecision.reject
        elif score >= 40:
            decision = RiskDecision.review
        else:
            decision = RiskDecision.approve

        return RiskResult(
            application_id=application_id,
            score=score,
            decision=decision,
            breakdown=breakdown,
            evidence=evidence,
        )
