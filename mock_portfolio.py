import numpy as np
import pandas as pd


def generate_baseline_portfolio(num_facilities: int = 500, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a statistically sound, realistic baseline portfolio of Egyptian retail
    and SME credit facilities adhering to standard IFRS 9 staging distributions.
    """
    np.random.seed(random_seed)

    facility_types = ["personal_loan", "auto_loan", "sme_working_capital", "credit_card"]
    type_weights = [0.50, 0.20, 0.15, 0.15]

    # Staging allocation weights (Typical Egyptian retail banking portfolio distribution)
    # Stage 1: 80%, Stage 2: 14%, Stage 3 (NPL): 6%
    stage_choices = np.random.choice([1, 2, 3], size=num_facilities, p=[0.80, 0.14, 0.06])

    records = []
    for i, stage in enumerate(stage_choices, start=1):
        fac_type = np.random.choice(facility_types, p=type_weights)

        # Granted amount and outstanding balances depending on facility type
        if fac_type == "sme_working_capital":
            granted = float(np.random.uniform(250_000, 1_500_000))
        elif fac_type == "auto_loan":
            granted = float(np.random.uniform(150_000, 600_000))
        elif fac_type == "personal_loan":
            granted = float(np.random.uniform(30_000, 250_000))
        else:  # credit_card
            granted = float(np.random.uniform(10_000, 80_000))

        # Outstanding balance as a percentage of granted facility
        balance_ratio = np.random.uniform(0.30, 0.95)
        outstanding = round(granted * balance_ratio, 2)
        tenure_months = int(np.random.choice([12, 24, 36, 48, 60]))
        installment = round((outstanding / max(tenure_months, 1)) * 1.15, 2)

        # DPD and PD parameters based on IFRS 9 stage
        if stage == 1:
            dpd = int(np.random.choice([0, 0, 0, 5, 12, 20]))
            pd = float(np.clip(np.random.normal(0.025, 0.01), 0.005, 0.06))
        elif stage == 2:
            dpd = int(np.random.randint(31, 89))
            pd = float(np.clip(np.random.normal(0.14, 0.04), 0.065, 0.35))
        else:  # Stage 3
            dpd = int(np.random.randint(90, 360))
            pd = 1.0  # By regulatory definition, Default has PD = 1.0 (100%)

        # Standard unsecured / partially secured LGD
        lgd = 0.45 if fac_type != "auto_loan" else 0.30

        records.append({
            "facility_id": f"FAC-EG-{100000 + i}",
            "national_id": f"2{np.random.randint(80, 99):02d}{np.random.randint(1, 12):02d}{np.random.randint(1, 28):02d}{np.random.randint(10000, 99999)}",
            "facility_type": fac_type,
            "stage": stage,
            "granted_amount": round(granted, 2),
            "outstanding_balance": outstanding,
            "installment_amount": installment,
            "dpd": dpd,
            "pd": round(pd, 4),
            "lgd": round(lgd, 4),
            "ecl": round(pd * lgd * outstanding, 2),
        })

    return pd.DataFrame(records)


# Global singleton in-memory portfolio DataFrame
baseline_portfolio_df = generate_baseline_portfolio()
