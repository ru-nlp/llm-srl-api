import pytest
from pytest_asyncio import fixture as async_fixture
import json
import logging
from unittest.mock import patch
from pathlib import Path
from app.srl import SRLAnalyzer, settings

logger = logging.getLogger(__name__)

@pytest.fixture
def mock_spacy_model():
    """Mock spaCy model for testing."""
    class MockToken:
        def __init__(self, text, lemma_, pos_):
            self.text = text
            self.lemma_ = lemma_
            self.pos_ = pos_

    class MockSpacy:
        def __call__(self, text):
            # Common test cases
            token_map = {
                "боюсь": [("боюсь", "бояться", "VERB")],
                "Я боюсь темноты": [
                    ("Я", "я", "PRON"),
                    ("боюсь", "бояться", "VERB"),
                    ("темноты", "темнота", "NOUN")
                ],
                "Я боюсь за брата": [
                    ("Я", "я", "PRON"),
                    ("боюсь", "бояться", "VERB"),
                    ("за", "за", "ADP"),
                    ("брата", "брат", "NOUN")
                ],
                "Мне нравится этот фильм": [
                    ("Мне", "я", "PRON"),
                    ("нравится", "нравиться", "VERB"),
                    ("этот", "этот", "DET"),
                    ("фильм", "фильм", "NOUN")
                ]
            }
            
            # Find exact match first
            if text in token_map:
                return [MockToken(t[0], t[1], t[2]) for t in token_map[text]]
            
            # Default case - treat as single noun
            return [MockToken(text, text, "NOUN")]

    return MockSpacy()

@async_fixture
async def analyzer(mock_spacy_model):
    """Create SRLAnalyzer instance with real mappings but mocked spaCy."""
    # Use real mapping files from res directory
    res_dir = Path(__file__).parent.parent / "res"
    
    # Update settings to use real mapping files
    settings.ROLE_MAPPING_FILE = str(res_dir / "role-mapping.json")
    settings.FORM_MAPPING_FILE = str(res_dir / "form-mapping.json")
    settings.EXAMPLES_FILE = str(res_dir / "groupped_examples.json")
    
    # Create analyzer with mocked spaCy but real mappings
    with patch('spacy.load', return_value=mock_spacy_model):
        analyzer = SRLAnalyzer()
        return analyzer

@pytest.mark.asyncio
async def test_no_relevant_predicates(analyzer):
    """Test analysis of text without relevant predicates."""
    result = await analyzer.analyze("простой текст")
    assert result["has_relevant_predicates"] is False
    assert not result["predicates"]
    assert not result["lemmas"]
    assert not result["roles"]

@pytest.mark.asyncio
async def test_fear_verb_with_object(analyzer, caplog):
    """Test analysis of fear verb with direct object."""
    caplog.set_level(logging.DEBUG)
    logger.info("\n=== Testing: Fear Verb with Object ===")
    
    result = await analyzer.analyze("Я боюсь темноты")
    logger.info(f"\nAnalysis result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    assert result["has_relevant_predicates"] is True
    assert result["predicates"] == ["боюсь"]
    assert result["lemmas"] == ["бояться"]
    assert len(result["roles"]) >= 1, "Should have at least one role"
    
    roles = {role["arg_role"]: role for role in result["roles"]}
    assert "Experiencer" in roles, "Should have Experiencer role"
    assert roles["Experiencer"]["arg_phrase_or_clause"] == "Я"

@pytest.mark.asyncio
async def test_fear_verb_with_deliberative(analyzer, caplog):
    """Test analysis of fear verb with deliberative argument."""
    caplog.set_level(logging.DEBUG)
    logger.info("\n=== Testing: Fear Verb with Deliberative ===")
    
    result = await analyzer.analyze("Я боюсь за брата")
    logger.info(f"\nAnalysis result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    assert result["has_relevant_predicates"] is True
    assert result["predicates"] == ["боюсь"]
    assert result["lemmas"] == ["бояться"]
    assert len(result["roles"]) >= 1, "Should have at least one role"
    
    roles = {role["arg_role"]: role for role in result["roles"]}
    assert "Experiencer" in roles, "Should have Experiencer role"
    assert "Deliberative" in roles, "Should have Deliberative role"
    assert roles["Experiencer"]["arg_phrase_or_clause"] == "Я"
    assert "брата" in roles["Deliberative"]["arg_phrase_or_clause"]

@pytest.mark.asyncio
async def test_like_verb(analyzer, caplog):
    """Test analysis of like/please verb."""
    caplog.set_level(logging.DEBUG)
    logger.info("\n=== Testing: Like/Please Verb ===")
    
    result = await analyzer.analyze("Мне нравится этот фильм")
    logger.info(f"\nAnalysis result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    assert result["has_relevant_predicates"] is True
    assert result["predicates"] == ["нравится"]
    assert result["lemmas"] == ["нравиться"]
    assert len(result["roles"]) >= 1, "Should have at least one role"
    
    roles = {role["arg_role"]: role for role in result["roles"]}
    assert "Experiencer" in roles, "Should have Experiencer role"
    assert "Object" in roles, "Should have Object role"
    assert roles["Experiencer"]["arg_phrase_or_clause"] == "Мне"
    assert "фильм" in roles["Object"]["arg_phrase_or_clause"]

@pytest.mark.asyncio
async def test_error_handling(analyzer, caplog):
    """Test handling of API errors with malformed input."""
    caplog.set_level(logging.DEBUG)
    logger.info("\n=== Testing: Error Handling ===")
    
    # Use malformed input that should cause the LLM to return a Not-Applicable role
    result = await analyzer.analyze("Я боюсь")  # Incomplete sentence
    logger.info(f"\nAnalysis result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    assert result["has_relevant_predicates"] is True
    assert result["predicates"] == ["боюсь"]
    assert result["lemmas"] == ["бояться"]
    
    # The roles should either be empty or contain a Not-Applicable role
    if result.get("roles"):
        for role in result["roles"]:
            assert isinstance(role, dict), "Each role should be a dictionary"
            assert "arg_role" in role, "Each role should have arg_role" 