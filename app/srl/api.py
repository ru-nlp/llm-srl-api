from fastapi import APIRouter, Depends
from typing import List
import logging
from functools import lru_cache

from .models import SRLRequest, SRLResponse
from .analyzer import SRLAnalyzer

# Get module logger
logger = logging.getLogger("app.srl.api")

router = APIRouter(prefix="/srl", tags=["Semantic Role Labeling"])

@lru_cache(maxsize=None)
def get_analyzer():
    """Dependency to get SRL analyzer instance.
    
    This function is cached to reuse the same analyzer (and spaCy model)
    across requests within the same worker process.
    """
    logger.debug("Creating or retrieving cached SRLAnalyzer instance")
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
    logger.info(f"Analyzing text: {request.text}")
    result = await analyzer.analyze(request.text)
    logger.info(f"Analysis completed with {len(result.get('roles', []))} roles found")
    return SRLResponse(**result) 