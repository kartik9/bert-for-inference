from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import uuid

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
    agent_identifier: str  # GPT ID, config path, etc.
    assessment_level: AssessmentLevel = AssessmentLevel.standard

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

async def run_assessment(assessment_id: str, request: AssessmentRequest):
    """Background task to run the assessment"""
    assessments_store[assessment_id]["status"] = "running"

    try:
        # Import assessment components
        from ...intake.models import AgentMetadata, AgentType, ToolDefinition, ToolCapability
        from ...scoring.aivss import AIVSSScorer
        from ...analysis.dynamic.suites.prompt_injection import PromptInjectionSuite

        # Create mock agent metadata for demo
        agent = AgentMetadata(
            agent_id=request.agent_identifier,
            name=f"Agent-{request.agent_identifier}",
            agent_type=AgentType(request.agent_type.value),
            tools=[
                ToolDefinition(
                    name="web_search",
                    description="Search the web",
                    capabilities=[ToolCapability.NETWORK_ACCESS]
                )
            ]
        )

        # Run dynamic tests (simplified for demo)
        pi_suite = PromptInjectionSuite()
        # In real implementation: pi_results = await pi_suite.run(agent_session)

        # Calculate scores
        scorer = AIVSSScorer()
        score = scorer.calculate(
            static_results=None,
            dynamic_results={},  # Would contain actual test results
            agent_metadata=agent
        )

        assessments_store[assessment_id]["status"] = "completed"
        assessments_store[assessment_id]["results"] = {
            "agent": agent.dict(),
            "score": {
                "overall": score.overall_score,
                "grade": score.letter_grade.value,
                "dimensions": score.dimensions.to_dict(),
                "trust_tier": score.trust_tier.value,
                "confidence": score.confidence,
                "flags": score.flags
            }
        }

    except Exception as e:
        assessments_store[assessment_id]["status"] = "failed"
        assessments_store[assessment_id]["error"] = str(e)
