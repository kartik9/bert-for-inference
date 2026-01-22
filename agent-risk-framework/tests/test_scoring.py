import pytest
from src.scoring.aivss import AIVSSScorer, LetterGrade, TrustTier, DimensionScores
from src.intake.models import AgentMetadata, AgentType, ToolDefinition, ToolCapability

def test_aivss_scorer_basic():
    """Test basic AIVSS scoring"""
    scorer = AIVSSScorer()

    # Create a simple agent with minimal capabilities
    agent = AgentMetadata(
        agent_id="test-001",
        name="Test Agent",
        agent_type=AgentType.CUSTOM,
        description="A test agent",
        developer="Test Developer",
        tools=[]
    )

    score = scorer.calculate(
        static_results=None,
        dynamic_results={},
        agent_metadata=agent
    )

    # Check that score components exist
    assert score.overall_score >= 0
    assert score.overall_score <= 100
    assert isinstance(score.letter_grade, LetterGrade)
    assert isinstance(score.trust_tier, TrustTier)
    assert 0 <= score.confidence <= 1

def test_letter_grade_assignment():
    """Test letter grade thresholds"""
    scorer = AIVSSScorer()

    assert scorer._to_letter_grade(95) == LetterGrade.A
    assert scorer._to_letter_grade(85) == LetterGrade.B
    assert scorer._to_letter_grade(75) == LetterGrade.C
    assert scorer._to_letter_grade(65) == LetterGrade.D
    assert scorer._to_letter_grade(55) == LetterGrade.F

def test_dangerous_capabilities_reduce_score():
    """Test that dangerous capabilities reduce autonomy score"""
    scorer = AIVSSScorer()

    # Agent with code execution
    dangerous_agent = AgentMetadata(
        agent_id="dangerous-001",
        name="Dangerous Agent",
        agent_type=AgentType.CUSTOM,
        tools=[
            ToolDefinition(
                name="code_exec",
                description="Execute code",
                capabilities=[ToolCapability.CODE_EXECUTION]
            )
        ]
    )

    # Agent without dangerous capabilities
    safe_agent = AgentMetadata(
        agent_id="safe-001",
        name="Safe Agent",
        agent_type=AgentType.CUSTOM,
        tools=[]
    )

    dangerous_score = scorer.calculate(None, {}, dangerous_agent)
    safe_score = scorer.calculate(None, {}, safe_agent)

    # Dangerous agent should have lower autonomy score (higher risk)
    assert dangerous_score.dimensions.autonomy_risk < safe_score.dimensions.autonomy_risk

def test_transparency_score_with_documentation():
    """Test that documentation improves transparency score"""
    scorer = AIVSSScorer()

    # Well-documented agent
    documented_agent = AgentMetadata(
        agent_id="doc-001",
        name="Documented Agent",
        agent_type=AgentType.CUSTOM,
        description="This is a well-documented agent",
        developer="Known Developer",
        version="2.0.0",
        system_prompt="You are a helpful assistant",
        tools=[]
    )

    # Poorly documented agent
    undocumented_agent = AgentMetadata(
        agent_id="undoc-001",
        name="Undocumented Agent",
        agent_type=AgentType.CUSTOM,
        tools=[]
    )

    doc_score = scorer.calculate(None, {}, documented_agent)
    undoc_score = scorer.calculate(None, {}, undocumented_agent)

    # Documented agent should have higher transparency score
    assert doc_score.dimensions.transparency > undoc_score.dimensions.transparency

def test_dimension_scores_to_dict():
    """Test dimension scores conversion to dictionary"""
    dims = DimensionScores(
        security=85.5,
        privacy=90.2,
        reliability=75.8,
        transparency=80.0,
        autonomy_risk=70.3
    )

    dim_dict = dims.to_dict()

    assert dim_dict["security"] == 85.5
    assert dim_dict["privacy"] == 90.2
    assert dim_dict["reliability"] == 75.8
    assert dim_dict["transparency"] == 80.0
    assert dim_dict["autonomy_risk"] == 70.3

def test_trust_tier_assignment():
    """Test trust tier assignment based on scores"""
    scorer = AIVSSScorer()

    # High-security agent without code execution
    trusted_agent = AgentMetadata(
        agent_id="trusted-001",
        name="Trusted Agent",
        agent_type=AgentType.CUSTOM,
        tools=[]
    )

    # Create mock results with high security
    mock_results = {}

    score = scorer.calculate(None, mock_results, trusted_agent)

    # Should be at least Basic tier for a safe agent
    assert score.trust_tier.value >= TrustTier.BASIC

def test_flags_generation():
    """Test that flags are generated for security issues"""
    scorer = AIVSSScorer()

    # Agent with many risky capabilities
    risky_agent = AgentMetadata(
        agent_id="risky-001",
        name="Risky Agent",
        agent_type=AgentType.CUSTOM,
        tools=[
            ToolDefinition(
                name="file_access",
                description="File operations",
                capabilities=[ToolCapability.FILE_READ, ToolCapability.DATABASE_ACCESS]
            ),
            ToolDefinition(
                name="code_runner",
                description="Run code",
                capabilities=[ToolCapability.CODE_EXECUTION, ToolCapability.SHELL]
            )
        ]
    )

    score = scorer.calculate(None, {}, risky_agent)

    # Should have some flags due to risky capabilities
    assert len(score.flags) > 0
