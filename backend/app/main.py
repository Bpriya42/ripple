from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Ripple API",
    version="0.1.0",
    description=(
        "Deterministic, evidence-backed causal explanations for energy news. "
        "This Milestone 1 API serves explicitly marked fixtures only."
    ),
)
app.include_router(router)
