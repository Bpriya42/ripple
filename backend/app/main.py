from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import frontend_origins

app = FastAPI(
    title="Ripple API",
    version="0.1.0",
    description=(
        "Deterministic, evidence-backed causal explanations for energy news. "
        "Stories may be explicitly marked fixtures or come from live GDELT "
        "ingestion; every displayed claim comes from the deterministic "
        "publication policy, never from a language model."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins(),
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(router)
