"""
Semantic Role Labeling (SRL) module.

This module provides functionality for analyzing Russian text and extracting semantic roles
using spaCy for preprocessing and T-Lite LLM for role extraction.
"""

from .api import router
from .analyzer import SRLAnalyzer
from .models import SRLRequest, SRLResponse, SemanticRole, SemanticRoleMarkup

__all__ = [
    'router',
    'SRLAnalyzer',
    'SRLRequest',
    'SRLResponse',
    'SemanticRole',
    'SemanticRoleMarkup'
] 