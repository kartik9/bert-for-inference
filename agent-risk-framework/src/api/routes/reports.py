from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from .assessments import assessments_store

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

@router.get("/{assessment_id}/nutrition-label", response_class=HTMLResponse)
async def get_nutrition_label_html(assessment_id: str):
    """Get nutrition label in HTML format"""
    if assessment_id not in assessments_store:
        raise HTTPException(status_code=404, detail="Assessment not found")

    assessment = assessments_store[assessment_id]

    if assessment["status"] != "completed":
        raise HTTPException(status_code=400, detail="Assessment not yet completed")

    try:
        from ...intake.models import AgentMetadata
        from ...scoring.aivss import AIVSSScore, LetterGrade, TrustTier, DimensionScores
        from ...reporting.nutrition_label import NutritionLabelGenerator

        # Reconstruct objects from stored dict
        results = assessment["results"]
        agent = AgentMetadata(**results["agent"])

        # Reconstruct score
        score_data = results["score"]
        score = AIVSSScore(
            overall_score=score_data["overall"],
            letter_grade=LetterGrade(score_data["grade"]),
            dimensions=DimensionScores(**score_data["dimensions"]),
            trust_tier=TrustTier(score_data["trust_tier"]),
            confidence=score_data["confidence"],
            flags=score_data["flags"]
        )

        generator = NutritionLabelGenerator()
        html = generator.generate_html(agent, score)

        return HTMLResponse(content=html)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating label: {str(e)}")

@router.get("/{assessment_id}/nutrition-label.json")
async def get_nutrition_label_json(assessment_id: str):
    """Get nutrition label in JSON format"""
    if assessment_id not in assessments_store:
        raise HTTPException(status_code=404, detail="Assessment not found")

    assessment = assessments_store[assessment_id]

    if assessment["status"] != "completed":
        raise HTTPException(status_code=400, detail="Assessment not yet completed")

    try:
        from ...intake.models import AgentMetadata
        from ...scoring.aivss import AIVSSScore, LetterGrade, TrustTier, DimensionScores
        from ...reporting.nutrition_label import NutritionLabelGenerator

        # Reconstruct objects from stored dict
        results = assessment["results"]
        agent = AgentMetadata(**results["agent"])

        # Reconstruct score
        score_data = results["score"]
        score = AIVSSScore(
            overall_score=score_data["overall"],
            letter_grade=LetterGrade(score_data["grade"]),
            dimensions=DimensionScores(**score_data["dimensions"]),
            trust_tier=TrustTier(score_data["trust_tier"]),
            confidence=score_data["confidence"],
            flags=score_data["flags"]
        )

        generator = NutritionLabelGenerator()
        json_output = generator.generate_json(agent, score)

        return JSONResponse(content=json_output)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating label: {str(e)}")
