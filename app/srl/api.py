from fastapi import APIRouter, Depends
from typing import List

from .models import SRLRequest, SRLResponse
from .analyzer import SRLAnalyzer

router = APIRouter(prefix="/srl", tags=["Semantic Role Labeling"])

async def get_analyzer():
    """Dependency to get SRL analyzer instance."""
    return SRLAnalyzer()

@router.post("/analyze", response_model=SRLResponse)
async def analyze_text(
    request: SRLRequest,
    analyzer: SRLAnalyzer = Depends(get_analyzer)
) -> SRLResponse:
    """
    Analyze text for semantic roles.
    
    This endpoint performs semantic role labeling on the input text:
    1. Checks if text contains relevant predicates
    2. If yes, extracts predicates and their lemmas
    3. Determines predicate group
    4. Uses LLM to extract semantic roles
    
    Args:
        request: SRLRequest containing text to analyze
        analyzer: SRLAnalyzer instance (injected)
        
    Returns:
        SRLResponse containing analysis results
    """
    result = await analyzer.analyze(request.text)
    return SRLResponse(**result) 