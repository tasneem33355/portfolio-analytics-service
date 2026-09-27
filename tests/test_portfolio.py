import pytest
from src.analytics import stress_test, build_stress_curve


def test_stress_test_increases_pd():
    baseline_pd = 0.04
    result = stress_test(
        portfolio_exposure=10_000_000,
        baseline_pd=baseline_pd,
        lgd=0.45,
        inflation_shock=0.10,
        rate_hike_bps=300,
        unemployment_shock=0.03,
    )
    assert result["stressed_pd"] >= baseline_pd
    assert result["stressed_ecl"] >= result["baseline_ecl"]
    assert result["ecl_delta"] >= 0


def test_build_stress_curve():
    curve = build_stress_curve(
        portfolio_exposure=5_000_000,
        baseline_pd=0.03,
        lgd=0.45,
    )
    assert len(curve) == 6
    assert curve[-1]["stressed_pd"] >= curve[0]["stressed_pd"]
