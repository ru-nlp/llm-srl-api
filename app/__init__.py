"""
Semantic Role Labeling API for Russian language using LLM and spaCy
"""

from .logging import setup_rich_logging
setup_rich_logging()  # Initialize logging first

import logging
logger = logging.getLogger("app")  # Get module logger

from . import config  # Then load config
from . import srl  # Finally load the application modules

logger.info("Application initialization completed") 