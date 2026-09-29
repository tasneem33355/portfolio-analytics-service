"""
Decision Log Reader Module
Loads audited underwriting decisions from the core database for portfolio tracking.
"""

import os
import sqlite3
from typing import Optional
import pandas as pd


def load_scored_decisions(db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load logged underwriting decisions.
    Gracefully returns an empty DataFrame if the physical database is not yet connected.
    Column aliases ensure compatibility with the CrediX schema.sql naming conventions.
    """
    if db_path is None:
        db_path = os.getenv("DECISION_LOG_DB_PATH", "database/credix_core.db")

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            query = """
                SELECT
                    decision_id             AS id,
                    application_id,
                    national_id,
                    model_version,
                    default_probability     AS probability_of_default,
                    credit_score,
                    final_decision          AS decision,
                    requested_amount        AS approved_amount,
                    approved_tenure_months,
                    dti_ratio,
                    fraud_risk_score,
                    is_anomaly,
                    created_at
                FROM decision_audit_logs
                ORDER BY created_at DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            if not df.empty:
                return df
        except Exception:
            pass

    return pd.DataFrame(columns=[
        "id", "application_id", "national_id", "model_version",
        "probability_of_default", "credit_score", "decision",
        "approved_amount", "approved_tenure_months", "dti_ratio",
        "fraud_risk_score", "is_anomaly", "created_at"
    ])
