from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import uuid
import os

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])

class AgentTypeInput(str, Enum):
    openai_gpt = "openai_gpt"
    langchain = "langchain"
    mcp_server = "mcp_server"

class AssessmentLevel(str, Enum):
    quick = "quick"      # Static only
    standard = "standard"  # Static + core dynamic
    comprehensive = "comprehensive"  # All tests

class AssessmentRequest(BaseModel):
    agent_type: AgentTypeInput
    agent_identifier: str  # GPT ID, URL, config path, etc.
    assessment_level: AssessmentLevel = AssessmentLevel.standard
    openai_api_key: Optional[str] = None  # Optional override for API key

class AssessmentResponse(BaseModel):
    assessment_id: str
    status: str
    message: str

# In-memory store for demo
assessments_store = {}

@router.post("/", response_model=AssessmentResponse)
async def create_assessment(request: AssessmentRequest, background_tasks: BackgroundTasks):
    """Start a new agent risk assessment"""
    assessment_id = str(uuid.uuid4())[:8]

    assessments_store[assessment_id] = {
        "status": "queued",
        "request": request.dict(),
        "results": None
    }

    # Queue for background processing
    background_tasks.add_task(run_assessment, assessment_id, request)

    return AssessmentResponse(
        assessment_id=assessment_id,
        status="queued",
        message=f"Assessment queued. Check status at /api/v1/assessments/{assessment_id}"
    )

@router.get("/{assessment_id}")
async def get_assessment(assessment_id: str):
    """Get assessment status and results"""
    if assessment_id not in assessments_store:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return assessments_store[assessment_id]

@router.get("/gpts/featured")
async def get_featured_gpts():
    """Get a list of featured GPTs from ChatGPT store"""
    from ...intake.connectors.openai_gpt import get_featured_gpts
    return {"featured_gpts": get_featured_gpts()}

async def run_assessment(assessment_id: str, request: AssessmentRequest):
    """Background task to run the assessment"""
    assessments_store[assessment_id]["status"] = "running"

    try:
        # Import assessment components
        from ...intake.models import AgentMetadata, AgentType
        from ...scoring.aivss import AIVSSScorer
        from ...analysis.dynamic.suites.prompt_injection import PromptInjectionSuite
        from ...intake.connectors.openai_gpt import OpenAIGPTConnector
        from ...analysis.dynamic.agent_session import MockAgentSession
        from ...config import settings

        agent_metadata = None
        agent_session = None
        dynamic_results = {}

        # Handle different agent types
        if request.agent_type == AgentTypeInput.openai_gpt:
            # Get API key from request or environment
            api_key = request.openai_api_key or settings.openai_api_key

            if not api_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY in .env or pass openai_api_key in request."
                )

            # Create connector and fetch metadata
            connector = OpenAIGPTConnector(api_key=api_key)
            agent_metadata = await connector.fetch_metadata(request.agent_identifier)

            # Create session for live testing
            agent_session = await connector.create_session(request.agent_identifier)

        else:
            # For other agent types, use mock for now
            agent_metadata = AgentMetadata(
                agent_id=request.agent_identifier,
                name=f"Agent-{request.agent_identifier}",
                agent_type=AgentType(request.agent_type.value),
                tools=[]
            )
            agent_session = MockAgentSession(agent_metadata.name)

        # Run dynamic tests if assessment level requires it
        if request.assessment_level in [AssessmentLevel.standard, AssessmentLevel.comprehensive]:
            # Run prompt injection tests
            pi_suite = PromptInjectionSuite()
            pi_results = await pi_suite.run(agent_session)
            dynamic_results["prompt_injection"] = pi_results

        # Calculate scores
        scorer = AIVSSScorer()
        score = scorer.calculate(
            static_results=None,
            dynamic_results=dynamic_results,
            agent_metadata=agent_metadata
        )

        # Store results
        assessments_store[assessment_id]["status"] = "completed"
        assessments_store[assessment_id]["results"] = {
            "agent": agent_metadata.model_dump(),
            "score": {
                "overall": score.overall_score,
                "grade": score.letter_grade.value,
                "dimensions": score.dimensions.to_dict(),
                "trust_tier": score.trust_tier.value,
                "confidence": score.confidence,
                "flags": score.flags
            },
            "test_results": {
                "prompt_injection": {
                    "total_tests": dynamic_results.get("prompt_injection").total_tests if dynamic_results.get("prompt_injection") else 0,
                    "passed": dynamic_results.get("prompt_injection").passed if dynamic_results.get("prompt_injection") else 0,
                    "failed": dynamic_results.get("prompt_injection").failed if dynamic_results.get("prompt_injection") else 0,
                    "pass_rate": dynamic_results.get("prompt_injection").pass_rate if dynamic_results.get("prompt_injection") else 0,
                    "critical_findings": len(dynamic_results.get("prompt_injection").critical_findings) if dynamic_results.get("prompt_injection") else 0,
                    "high_findings": len(dynamic_results.get("prompt_injection").high_findings) if dynamic_results.get("prompt_injection") else 0,
                } if dynamic_results.get("prompt_injection") else None
            }
        }

    except Exception as e:
        import traceback
        assessments_store[assessment_id]["status"] = "failed"
        assessments_store[assessment_id]["error"] = str(e)
        assessments_store[assessment_id]["traceback"] = traceback.format_exc()
