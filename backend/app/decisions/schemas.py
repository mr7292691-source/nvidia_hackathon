from __future__ import annotations

from pydantic import BaseModel


class LifeSafetyGuidance(BaseModel):
    event_id: str
    guidance_text: str
    evidence_ref: str  # event_id, ties output back to the same evidence record
    approved: bool = False


class PolicyExposure(BaseModel):
    policy_id: str
    tiv_usd: float
    limit_usd: float
    deductible_usd: float
    estimated_exposure_usd: float


class InsurerExposureReport(BaseModel):
    event_id: str
    policies: list[PolicyExposure]
    total_estimated_exposure_usd: float
    evidence_ref: str
    approved: bool = False
