"""
Deterministic TIV / limit / deductible math per slide 3: "insurer exposure
from deterministic TIV, limit and deductible math." Intentionally plain
arithmetic — this function must never call an LLM. Its inputs come from
app/agents/tools/portfolio_tools.py (the synthetic, de-identified overlay).
"""
from __future__ import annotations

from app.decisions.schemas import InsurerExposureReport, PolicyExposure


def estimate_exposure(policy: dict, *, damage_severity_factor: float) -> PolicyExposure:
    """
    Simple, auditable model: exposure = min(limit, damage_severity_factor * TIV) - deductible,
    floored at 0. damage_severity_factor in [0, 1] should come from a
    deterministic mapping of the vision specialist's damage_assessment
    category — NOT from free-form LLM text directly (TODO: define that
    mapping once the vision NIM's structured output schema is settled).
    """
    tiv = policy["tiv_usd"]
    limit = policy["limit_usd"]
    deductible = policy["deductible_usd"]

    raw_exposure = min(limit, damage_severity_factor * tiv)
    exposure = max(0.0, raw_exposure - deductible)

    return PolicyExposure(
        policy_id=policy["policy_id"],
        tiv_usd=tiv,
        limit_usd=limit,
        deductible_usd=deductible,
        estimated_exposure_usd=round(exposure, 2),
    )


def build_insurer_exposure_report(
    *, event_id: str, policies: list[dict], damage_severity_factor: float
) -> InsurerExposureReport:
    line_items = [estimate_exposure(p, damage_severity_factor=damage_severity_factor) for p in policies]
    return InsurerExposureReport(
        event_id=event_id,
        policies=line_items,
        total_estimated_exposure_usd=round(sum(p.estimated_exposure_usd for p in line_items), 2),
        evidence_ref=event_id,
    )
