from app.decisions.insurer_exposure import build_insurer_exposure_report, estimate_exposure


def test_estimate_exposure_below_limit():
    policy = {"policy_id": "P1", "tiv_usd": 100_000, "limit_usd": 100_000, "deductible_usd": 1_000}
    result = estimate_exposure(policy, damage_severity_factor=0.5)
    # 0.5 * 100_000 = 50_000, minus 1_000 deductible = 49_000
    assert result.estimated_exposure_usd == 49_000


def test_estimate_exposure_capped_by_limit():
    policy = {"policy_id": "P2", "tiv_usd": 1_000_000, "limit_usd": 100_000, "deductible_usd": 5_000}
    result = estimate_exposure(policy, damage_severity_factor=1.0)
    # min(100_000, 1_000_000) - 5_000 = 95_000
    assert result.estimated_exposure_usd == 95_000


def test_estimate_exposure_floored_at_zero():
    policy = {"policy_id": "P3", "tiv_usd": 10_000, "limit_usd": 10_000, "deductible_usd": 50_000}
    result = estimate_exposure(policy, damage_severity_factor=1.0)
    assert result.estimated_exposure_usd == 0.0


def test_build_insurer_exposure_report_totals():
    policies = [
        {"policy_id": "P1", "tiv_usd": 100_000, "limit_usd": 100_000, "deductible_usd": 1_000},
        {"policy_id": "P2", "tiv_usd": 200_000, "limit_usd": 150_000, "deductible_usd": 2_000},
    ]
    report = build_insurer_exposure_report(
        event_id="evt_test", policies=policies, damage_severity_factor=0.5
    )
    assert report.event_id == "evt_test"
    assert len(report.policies) == 2
    assert report.total_estimated_exposure_usd == sum(p.estimated_exposure_usd for p in report.policies)
