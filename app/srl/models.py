from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Annotated

class SemanticRole(BaseModel):
    """A single semantic role annotation."""
    role: Literal["Cause", "Experiencer", "Causator", "Deliberative", "Instrument", "Object", "Not-Applicable"]
    text: Annotated[str, Field(min_length=1, max_length=64)]

    # Hidden fields for LLM processing
    _short_reasoning: str | None = None
    _main_word: str | None = None

class SemanticRoleMarkup(BaseModel):
    """Complete semantic role markup for a text."""
    roles: List[SemanticRole]
    model_config = {
        "title": "SemanticRoleMarkup",
        "description": "Semantic Role Markup"
    }

class SRLRequest(BaseModel):
    """Request model for SRL analysis."""
    text: str = Field(..., description="Text to analyze for semantic roles")

class SRLResponse(BaseModel):
    """Response model for SRL analysis."""
    text: str = Field(..., description="Original text that was analyzed")
    predicates: List[str] = Field(default_factory=list, description="Found predicates in the text")
    lemmas: List[str] = Field(default_factory=list, description="Lemmatized forms of found predicates")
    roles: List[SemanticRole] = Field(default_factory=list, description="Extracted semantic roles")
    has_relevant_predicates: bool = Field(default=False, description="Whether text contains relevant predicates") 