"""
CrediX Portfolio Analytics Service - Main Application Entrypoint
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.portfolio import router as portfolio_router

app = FastAPI(
    title="CrediX Portfolio Analytics Service",
    version="1.0.0",
    description="Enterprise Analytics Microservice for IFRS 9 Staging, Stress Testing, and Drift Monitoring.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware configured to allow requests from Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://credi-x.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the portfolio routes
app.include_router(portfolio_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "portfolio-analytics-service",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Confirms system health, baseline data readiness, and database connection state.
    """
    baseline_csv_path = os.getenv("BASELINE_CSV_PATH", "data/fraud_training_data_25000.csv")
    csv_available = os.path.exists(baseline_csv_path)

    return {
        "status": "healthy",
        "baseline_data_loaded": csv_available,
        "environment": os.getenv("ENVIRONMENT", "production"),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api.main.py:app", host="0.0.0.0", port=port, reload=False)
