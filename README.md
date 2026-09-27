# CrediX Portfolio Analytics Service

Enterprise microservice powering real-time credit portfolio analytics, macroeconomic stress testing, IFRS 9 staging, and population drift monitoring for the CrediX underwriting platform.

## Repository Architecture

```text
portfolio-analytics-service/
├── api/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entrypoint, CORS configuration, health checks
│   └── routes/
│       ├── __init__.py
│       └── portfolio.py         # REST endpoints for KPIs, stress tests, and drift
├── src/
│   ├── __init__.py
│   ├── analytics.py             # IFRS 9 ECL calculation, staging, and concentration logic
│   ├── drift_monitor.py         # Population Stability Index (PSI) baseline monitor
│   └── decision_log_reader.py   # Secure data access layer for audited model decisions
├── data/
│   ├── bank_data_sample_Ammar Elgazar.xlsx  # Reference banking portfolio workbook
│   └── fraud_training_data_25000.csv        # Baseline dataset for drift detection
├── tests/
│   ├── __init__.py
│   └── test_portfolio.py        # Automated test suite for stress testing engines
├── requirements.txt             # Production dependencies
├── Dockerfile                   # Cloud container build specification
├── .gitignore                   # Version control ignore rules
└── README.md                    # Service documentation
```

## API Specifications

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status and baseline verification |
| `GET` | `/api/v1/portfolio/kpis` | Core portfolio KPIs (Volume, Active Loans, NPL Ratio) |
| `GET` | `/api/v1/portfolio/scored-kpis` | ML underwriting metrics (Approval Rate, Average PD) |
| `GET` | `/api/v1/portfolio/concentration` | Risk exposure distribution by product and status |
| `POST` | `/api/v1/portfolio/stress-test` | Macroeconomic shock simulation (Inflation, Rates, Unemployment) |
| `GET` | `/api/v1/portfolio/drift` | Population Stability Index (PSI) drift monitoring |

## Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
uvicorn api.main.py:app --host 0.0.0.0 --port 8000 --reload

# 3. View API documentation
# Navigate to http://localhost:8000/docs
```

## Running Tests

```bash
pytest tests/
```

## Container Deployment

```bash
docker build -t portfolio-analytics-service .
docker run -p 8000:8000 portfolio-analytics-service
```
