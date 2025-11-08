"""
URL Trust and Safety Analysis API
A comprehensive AI-powered URL investigation system for safety researchers
"""

import os
import json
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl, Field
import httpx
from dotenv import load_dotenv

from url_analyzer import URLAnalyzer
from ai_agent import SafetyAnalysisAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="URL Safety Analysis API",
    description="AI-powered URL trust and safety investigation platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
url_analyzer = URLAnalyzer()
ai_agent = SafetyAnalysisAgent()


# Request/Response Models
class URLAnalysisRequest(BaseModel):
    url: str = Field(..., description="URL to analyze for trust and safety concerns")
    deep_analysis: bool = Field(default=True, description="Enable deep analysis mode")


class FollowUpRequest(BaseModel):
    url: str
    question: str
    previous_context: Optional[Dict[str, Any]] = None


class AnalysisStatus(BaseModel):
    status: str
    message: str
    progress: int
    data: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """API health check"""
    return {
        "service": "URL Safety Analysis API",
        "status": "operational",
        "version": "1.0.0"
    }


@app.post("/api/analyze")
async def analyze_url(request: URLAnalysisRequest):
    """
    Start URL safety analysis with streaming updates
    Returns Server-Sent Events (SSE) stream
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for real-time progress updates"""
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting URL analysis...', 'progress': 0})}\n\n"

            # Phase 1: Technical Analysis
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'Technical Analysis', 'progress': 10})}\n\n"

            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Gathering technical information about the URL...'})}\n\n"

            technical_data = await url_analyzer.analyze(request.url)

            yield f"data: {json.dumps({'type': 'data', 'category': 'technical', 'data': technical_data, 'progress': 30})}\n\n"

            # Phase 2: AI Analysis Plan
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'AI Investigation Planning', 'progress': 35})}\n\n"

            # Create investigation plan
            plan = await ai_agent.create_investigation_plan(request.url, technical_data)

            yield f"data: {json.dumps({'type': 'plan', 'plan': plan, 'progress': 40})}\n\n"

            # Phase 3: Execute Investigation
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'Deep Investigation', 'progress': 45})}\n\n"

            # Stream AI reasoning and analysis
            async for update in ai_agent.investigate_url(request.url, technical_data, plan):
                yield f"data: {json.dumps(update)}\n\n"
                await asyncio.sleep(0.1)  # Small delay for smooth streaming

            # Phase 4: Generate Final Report
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'Generating Report', 'progress': 90})}\n\n"

            report = await ai_agent.generate_report(request.url, technical_data)

            yield f"data: {json.dumps({'type': 'report', 'report': report, 'progress': 100})}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'message': 'Analysis complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/followup")
async def followup_question(request: FollowUpRequest):
    """
    Handle follow-up questions about a previously analyzed URL
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Stream follow-up analysis"""
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your question...'})}\n\n"

            # Get AI response to follow-up
            async for update in ai_agent.answer_followup(
                request.url,
                request.question,
                request.previous_context
            ):
                yield f"data: {json.dumps(update)}\n\n"
                await asyncio.sleep(0.1)

            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            logger.error(f"Error during follow-up: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/health")
async def health_check():
    """Check API and dependencies health"""
    health_status = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "url_analyzer": "ready",
            "ai_agent": "ready" if ai_agent.is_configured() else "not_configured"
        }
    }
    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
