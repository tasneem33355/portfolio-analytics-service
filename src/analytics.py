"""
CrediX Portfolio Analytics Core Engine
Provides financial calculations for IFRS 9 staging, portfolio KPIs, concentration, and stress testing.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Dict, Any
import numpy as np
import pandas as pd


def load_core_banking_data(
    workbook_path: str = "data/bank_data_sample_Ammar Elgazar.xlsx",
    db_path: str = "database/credix_core.db"
) -> Dict[str, pd.DataFrame]:
    """
    Dual-source loader:
    1. Attempts to load live records from SQLite/Postgres core banking tables.
    2. Falls back to the packaged reference Excel workbook if DB is not attached.
    """
    empty = {
        "customers": pd.DataFrame(),
        "accounts": pd.DataFrame(),
        "transactions": pd.DataFrame(),
        "loans": pd.DataFrame(),
        "branches": pd.DataFrame(),
    }

    # 1. Try reading from SQLite Core Banking if available
    resolved_db = os.getenv("CORE_BANKING_DB_PATH", db_path)
    if os.path.exists(resolved_db):
        try:
            conn = sqlite3.connect(resolved_db)
            loans_df = pd.read_sql_query("SELECT * FROM loan_facilities", conn)
            cust_df = pd.read_sql_query("SELECT * FROM customers", conn)
            acc_df = pd.read_sql_query("SELECT * FROM accounts", conn)
            tx_df = pd.read_sql_query("SELECT * FROM transactions", conn)
            conn.close()

            if not loans_df.empty:
                return {
                    "customers": cust_df,
                    "accounts": acc_df,
                    "transactions": tx_df,
                    "loans": loans_df,
                    "branches": pd.DataFrame(),
                }
        except Exception:
            pass

    # 2. Fallback to reference Excel file
    resolved_wb = os.getenv("CORE_BANKING_EXCEL_PATH", workbook_path)
    if not os.path.exists(resolved_wb):
        return empty

    try:
        excel = pd.ExcelFile(resolved_wb)
    except Exception:
        return empty

    def read_sheet(name: str) -> pd.DataFrame:
        if name not in excel.sheet_names:
            return pd.DataFrame()
        try:
            return pd.read_excel(resolved_wb, sheet_name=name)
        except Exception:
            return pd.DataFrame()

    return {
        "customers": read_sheet("Customers"),
        "accounts": read_sheet("Accounts"),
        "transactions": read_sheet("Transactions"),
        "loans": read_sheet("Loans"),
        "branches": read_sheet("Branches"),
    }


def prepare_data(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Standardize dates and column names across all core dataframes."""
    result = {}
    for name, df in data.items():
        if df is None or df.empty:
            result[name] = pd.DataFrame()
            continue

        df = df.copy()
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        for col in df.columns:
            if "date" in col or col in ["dob", "opened", "timestamp"]:
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    pass

        result[name] = df
    return result


def calculate_portfolio_kpis(data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Calculate executive portfolio summary KPIs for the overview dashboard."""
    loans = data.get("loans", pd.DataFrame())
    customers = data.get("customers", pd.DataFrame())

    if loans.empty:
        return {
            "total_loans_count": 0,
            "total_portfolio_volume": 0.0,
            "average_loan_size": 0.0,
            "npl_ratio": 0.0,
            "performing_loans_count": 0,
            "npl_loans_count": 0,
        }

    amount_col = "amount" if "amount" in loans.columns else "loan_amount"
    if amount_col not in loans.columns:
        amount_col = loans.select_dtypes(include=[np.number]).columns[0] if len(loans.select_dtypes(include=[np.number]).columns) > 0 else None

    total_volume = float(loans[amount_col].sum()) if amount_col else 0.0
    total_count = len(loans)
    avg_size = float(loans[amount_col].mean()) if (amount_col and total_count > 0) else 0.0

    # Determine NPL based on status or dpd
    npl_mask = pd.Series(False, index=loans.index)
    if "status" in loans.columns:
        npl_mask = npl_mask | loans["status"].astype(str).str.lower().isin(["default", "npl", "bad", "charged-off"])
    if "dpd" in loans.columns:
        npl_mask = npl_mask | (loans["dpd"] >= 90)

    npl_count = int(npl_mask.sum())
    npl_ratio = float(npl_count / total_count) if total_count > 0 else 0.0

    return {
        "total_loans_count": total_count,
        "total_portfolio_volume": round(total_volume, 2),
        "average_loan_size": round(avg_size, 2),
        "npl_ratio": round(npl_ratio, 4),
        "performing_loans_count": total_count - npl_count,
        "npl_loans_count": npl_count,
    }


def calculate_scored_portfolio_kpis(df_decisions: pd.DataFrame) -> Dict[str, Any]:
    """Metrics evaluated on ML model underwriting decisions."""
    if df_decisions.empty:
        return {
            "total_scored_applications": 0,
            "approval_rate": 0.0,
            "rejection_rate": 0.0,
            "average_model_pd": 0.0,
        }

    total = len(df_decisions)
    approvals = (df_decisions["decision"].str.upper() == "APPROVE").sum() if "decision" in df_decisions.columns else 0
    rejections = (df_decisions["decision"].str.upper() == "REJECT").sum() if "decision" in df_decisions.columns else 0
    avg_pd = float(df_decisions["probability_of_default"].mean()) if "probability_of_default" in df_decisions.columns else 0.0

    return {
        "total_scored_applications": total,
        "approval_rate": round(float(approvals / total), 4) if total > 0 else 0.0,
        "rejection_rate": round(float(rejections / total), 4) if total > 0 else 0.0,
        "average_model_pd": round(avg_pd, 4),
    }


def calculate_concentration(loans: pd.DataFrame) -> Dict[str, Any]:
    """Calculate loan distribution across categories."""
    if loans is None or loans.empty:
        return {"by_product": {}, "by_status": {}}

    result = {}
    type_col = next((c for c in ["type", "loan_type", "product"] if c in loans.columns), None)
    if type_col:
        result["by_product"] = loans[type_col].value_counts().to_dict()
    else:
        result["by_product"] = {}

    status_col = next((c for c in ["status", "loan_status"] if c in loans.columns), None)
    if status_col:
        result["by_status"] = loans[status_col].value_counts().to_dict()
    else:
        result["by_status"] = {}

    return result


def stress_test(
    portfolio_exposure: float,
    baseline_pd: float,
    lgd: float = 0.45,
    inflation_shock: float = 0.05,
    rate_hike_bps: float = 200.0,
    unemployment_shock: float = 0.02,
) -> Dict[str, float]:
    """
    Macroeconomic stress testing engine simulating credit portfolio impairment.
    Calculates Stressed PD and Stressed Expected Credit Loss (ECL).
    """
    # Elasticity weights calibrated for emerging/MENA banking retail portfolios
    pd_shift = (inflation_shock * 0.4) + ((rate_hike_bps / 10000.0) * 0.6) + (unemployment_shock * 0.5)
    stressed_pd = float(np.clip(baseline_pd * (1.0 + pd_shift), 0.0, 1.0))

    baseline_ecl = portfolio_exposure * baseline_pd * lgd
    stressed_ecl = portfolio_exposure * stressed_pd * lgd
    ecl_delta = stressed_ecl - baseline_ecl

    return {
        "portfolio_exposure": round(portfolio_exposure, 2),
        "baseline_pd": round(baseline_pd, 4),
        "stressed_pd": round(stressed_pd, 4),
        "pd_increase_pct": round(float((stressed_pd - baseline_pd) / baseline_pd * 100), 2) if baseline_pd > 0 else 0.0,
        "baseline_ecl": round(baseline_ecl, 2),
        "stressed_ecl": round(stressed_ecl, 2),
        "ecl_delta": round(ecl_delta, 2),
        "capital_coverage_needed": round(stressed_ecl / portfolio_exposure, 4) if portfolio_exposure > 0 else 0.0,
    }


def build_stress_curve(
    portfolio_exposure: float,
    baseline_pd: float,
    lgd: float = 0.45
) -> list[Dict[str, float]]:
    """Build multi-point sensitivity curve across increasing rate shock steps."""
    curve = []
    for rate_bps in [0, 100, 200, 300, 500, 750]:
        res = stress_test(
            portfolio_exposure=portfolio_exposure,
            baseline_pd=baseline_pd,
            lgd=lgd,
            rate_hike_bps=float(rate_bps),
        )
        curve.append({
            "rate_hike_bps": rate_bps,
            "stressed_pd": res["stressed_pd"],
            "stressed_ecl": res["stressed_ecl"],
        })
    return curve
