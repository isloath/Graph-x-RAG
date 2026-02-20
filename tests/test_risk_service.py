import pytest

from app.models.schemas import RiskDecision
from app.services.risk_service import RiskService


@pytest.mark.asyncio
async def test_reject_threshold() -> None:
    svc = RiskService()
    result = await svc.score(
        application_id="APP-1",
        phone_degree=2,
        document_degree=2,
        device_degree=3,
        max_identifier_degree=5,
        community_size=5,
    )
    assert result.score == 150
    assert result.decision == RiskDecision.reject


@pytest.mark.asyncio
async def test_review_threshold() -> None:
    svc = RiskService()
    result = await svc.score(
        application_id="APP-2",
        phone_degree=2,
        document_degree=0,
        device_degree=0,
        max_identifier_degree=0,
        community_size=0,
    )
    assert result.score == 20
    assert result.decision == RiskDecision.approve


@pytest.mark.asyncio
async def test_mid_range_review() -> None:
    svc = RiskService()
    result = await svc.score(
        application_id="APP-3",
        phone_degree=2,
        document_degree=2,
        device_degree=0,
        max_identifier_degree=0,
        community_size=0,
    )
    assert result.score == 60
    assert result.decision == RiskDecision.review
