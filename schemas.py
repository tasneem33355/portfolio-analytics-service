from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# --- Health & Status Schemas ---
class HealthResponse(BaseModel):
    status: str = Field(default="ok", example="ok")
    service: str = Field(default="portfolio-analytics-service")
    version: str = Field(default="1.0.0")


# --- Portfolio Overall KPIs Schemas ---
class PortfolioKPIsResponse(BaseModel):
    total_active_loans: int = Field(..., description="Total active loan contracts in the portfolio")
    total_portfolio_exposure_egp: float = Field(..., description="Total Exposure at Default (EAD) in EGP")
    total_ecl_reserve_egp: float = Field(..., description="Total Expected Credit Loss provision in EGP")
    portfolio_coverage_ratio: float = Field(..., description="Coverage ratio (Total ECL / Total Exposure)")
    npl_ratio: float = Field(..., description="Non-Performing Loans ratio (Stage 3 Exposure / Total Exposure)")
    weighted_avg_pd: float = Field(..., description="Exposure-weighted Average Probability of Default")
    weighted_avg_lgd: float = Field(default=0.45, description="Regulatory baseline Loss Given Default")


# --- IFRS 9 Staging Breakdown Schemas ---
class StageDetail(BaseModel):
    stage: int = Field(..., description="Stage 1 (Performing), Stage 2 (Underperforming), Stage 3 (Defaulted)")
    stage_name: str = Field(..., description="Performing / Underperforming / Non-Performing (NPL)")
    loan_count: int = Field(..., description="Number of facilities in this stage")
    loan_count_pct: float = Field(..., description="Percentage of total loan count")
    total_exposure_egp: float = Field(..., description="Total outstanding balance in EGP")
    exposure_pct: float = Field(..., description="Percentage of total portfolio exposure")
    ecl_reserve_egp: float = Field(..., description="Total ECL provision assigned to this stage")
    avg_pd: float = Field(..., description="Average PD for this specific stage")


class StagingBreakdownResponse(BaseModel):
    stages: List[StageDetail]
    summary_note: str = Field(
        default="Stage 1: DPD < 30 | Stage 2: 30 <= DPD < 90 (SICR) | Stage 3: DPD >= 90 (NPL/Default)"
    )


# --- Transition / Roll-Rate Matrix Schemas ---
class TransitionMatrixResponse(BaseModel):
    observation_period: str = Field(default="Monthly Roll-Rate", example="Monthly Roll-Rate")
    from_stages: List[str] = Field(default=["Stage 1", "Stage 2", "Stage 3"])
    to_stages: List[str] = Field(default=["Stage 1", "Stage 2", "Stage 3", "Settled/Closed"])
    transition_probabilities: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Transition probability matrix from origin stage to destination stage over a 30-day window",
        example={
            "Stage 1": {"Stage 1": 0.942, "Stage 2": 0.043, "Stage 3": 0.003, "Settled/Closed": 0.012},
            "Stage 2": {"Stage 1": 0.125, "Stage 2": 0.690, "Stage 3": 0.165, "Settled/Closed": 0.020},
            "Stage 3": {"Stage 1": 0.010, "Stage 2": 0.040, "Stage 3": 0.930, "Settled/Closed": 0.020},
        },
    )


# --- Macroeconomic Stress Testing Schemas ---
class StressTestScenarioRequest(BaseModel):
    scenario_name: str = Field(
        default="Adverse Inflation & FX Shock",
        example="Adverse Inflation & FX Shock",
        description="Name or label of the macroeconomic stress test scenario",
    )
    pd_multiplier: float = Field(
        default=1.35,
        ge=0.5,
        le=5.0,
        description="Multiplicative stress factor applied to baseline PD (e.g. 1.35 = 35% increase in default risk)",
    )
    lgd_shift: float = Field(
        default=0.10,
        ge=-0.2,
        le=0.5,
        description="Additive stress shift to LGD (e.g. 0.10 means LGD moves from 0.45 to 0.55 due to collateral depreciation)",
    )
    unemployment_shock_pct: Optional[float] = Field(
        default=2.5, description="Simulated increase in Egyptian national unemployment rate"
    )


class StressTestResultResponse(BaseModel):
    scenario_name: str
    baseline_ecl_egp: float
    stressed_ecl_egp: float
    ecl_delta_egp: float
    ecl_percentage_change: float
    baseline_npl_ratio: float
    stressed_npl_ratio: float
    stressed_coverage_ratio: float
    capital_impact_summary_en: str
    capital_impact_summary_ar: str


# --- Custom Upload / Scoring Batch Schema ---
class FacilityItem(BaseModel):
    facility_id: str
    national_id: str
    facility_type: str = Field(default="personal_loan")
    granted_amount: float
    outstanding_balance: float
    installment_amount: float
    dpd: int = Field(default=0, description="Days Past Due")
    pd: float = Field(default=0.04, ge=0.0, le=1.0, description="Probability of Default")
    lgd: float = Field(default=0.45, ge=0.0, le=1.0, description="Loss Given Default")


class IngestBatchFacilitiesRequest(BaseModel):
    facilities: List[FacilityItem]


class IngestBatchFacilitiesResponse(BaseModel):
    status: str = "success"
    ingested_count: int
    total_exposure_egp: float
    message: str
