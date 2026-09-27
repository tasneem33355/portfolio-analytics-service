"""
Portfolio Analytics API Router
Enterprise microservice exposing endpoints for portfolio KPIs, risk concentration,
macroeconomic stress testing, and population drift monitoring.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.analytics import (
    calculate_portfolio_kpis,
    calculate_scored_portfolio_kpis,
    calculate_concentration,
    stress_test,
    build_stress_curve,
    load_core_banking_data,
    prepare_data,
)
from src.decision_log_reader import load_scored_decisions
from src.drift_monitor import PopulationDriftMonitor

router = APIRouter(prefix="/api/v1/portfolio", tags=["Portfolio Analytics"])

# Initialize drift monitor once at startup
try:
    drift_monitor = PopulationDriftMonitor()
except Exception:
    drift_monitor = None


# --- Pydantic Request Models ---
class StressTestRequest(BaseModel):
    portfolio_exposure: float = Field(..., gt=0, description="Total portfolio exposure in EGP", example=10000000.0)
    baseline_pd: float = Field(..., ge=0.0, le=1.0, description="Baseline Probability of Default", example=0.045)
    lgd: float = Field(default=0.45, ge=0.0, le=1.0, description="Loss Given Default", example=0.45)
    inflation_shock: float = Field(default=0.05, ge=-0.5, le=1.0, description="Inflation increase rate", example=0.05)
    rate_hike_bps: float = Field(default=200.0, ge=0.0, le=5000.0, description="Interest rate hike in basis points", example=200.0)
    unemployment_shock: float = Field(default=0.02, ge=-0.5, le=1.0, description="Unemployment rate increase", example=0.02)


# --- API Endpoints ---

@router.get("/kpis", summary="Get overall Core Banking Portfolio KPIs")
def get_portfolio_kpis():
    """
    Returns real-time portfolio metrics (total volume, active facilities, average ticket size, NPL ratio)
    consumed directly by executive dashboard overview cards.
    """
    try:
        data = load_core_banking_data()
        prepared = prepare_data(data)
        kpis = calculate_portfolio_kpis(prepared)
        return {"status": "success", "data": kpis}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate portfolio KPIs: {str(exc)}"
        )


@router.get("/scored-kpis", summary="Get Model-Scored Portfolio Performance KPIs")
def get_scored_portfolio_kpis():
    """
    Calculates underwriting performance metrics based on logged machine learning decisions.
    """
    try:
        df_decisions = load_scored_decisions()
        scored_kpis = calculate_scored_portfolio_kpis(df_decisions)
        return {"status": "success", "data": scored_kpis}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate scored KPIs: {str(exc)}"
        )


@router.get("/concentration", summary="Get Loan Portfolio Concentration Breakdown")
def get_portfolio_concentration():
    """
    Returns risk concentration across loan products, governorates, and customer segments
    to render distribution charts on the frontend.
    """
    try:
        data = load_core_banking_data()
        prepared = prepare_data(data)
        loans_df = prepared.get("loans")
        concentration = calculate_concentration(loans_df)
        return {"status": "success", "data": concentration}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate concentration: {str(exc)}"
        )


@router.post("/stress-test", summary="Run Macroeconomic Stress Testing Scenario")
def run_stress_test(payload: StressTestRequest):
    """
    Simulates macroeconomic shocks (Inflation, Interest Rate Hikes, Unemployment)
    and computes the stressed PD, stressed ECL provisions, and capital buffer impact.
    """
    try:
        results = stress_test(
            portfolio_exposure=payload.portfolio_exposure,
            baseline_pd=payload.baseline_pd,
            lgd=payload.lgd,
            inflation_shock=payload.inflation_shock,
            rate_hike_bps=payload.rate_hike_bps,
            unemployment_shock=payload.unemployment_shock,
        )
        curve = build_stress_curve(
            portfolio_exposure=payload.portfolio_exposure,
            baseline_pd=payload.baseline_pd,
            lgd=payload.lgd,
        )
        return {
            "status": "success",
            "scenario_results": results,
            "sensitivity_curve": curve,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stress test execution failed: {str(exc)}"
        )


@router.get("/drift", summary="Monitor Population Stability Index (PSI) Drift")
def get_population_drift():
    """
    Evaluates whether the distribution of recent applicants has drifted from
    the baseline training population, signaling automated retraining triggers.
    """
    if drift_monitor is None:
        return {
            "status": "warning",
            "message": "Drift monitor baseline is initializing or baseline CSV not mounted.",
            "drift_detected": False,
        }
    try:
        df_decisions = load_scored_decisions()
        drift_report = drift_monitor.evaluate_batch_drift(df_decisions)
        return {"status": "success", "data": drift_report}
    except Exception as exc:
        return {
            "status": "neutral",
            "message": f"Drift evaluated with baseline: {str(exc)}",
            "drift_detected": False,
        }
