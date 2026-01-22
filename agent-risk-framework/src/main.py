from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import assessments, reports

app = FastAPI(
    title="AI Agent Risk Assessment Framework",
    description="Automated security assessment and nutrition labeling for AI agents",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assessments.router)
app.include_router(reports.router)

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}
