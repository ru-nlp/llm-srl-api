import json
import spacy
import logging
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
from pathlib import Path

from ..config import settings
from .models import SemanticRoleMarkup

logger = logging.getLogger("app.srl.analyzer")

class SRLAnalyzer:
    """
    Semantic Role Labeling (SRL) analyzer that uses spaCy for preprocessing
    and T-Lite LLM for role extraction.
    """
    
    def __init__(self):
        """Initialize the analyzer with spaCy model and load mappings."""
        logger.info("Initializing SRL Analyzer")
        self.nlp = spacy.load(settings.SPACY_MODEL)
        self.role_mapping = self._load_json(settings.ROLE_MAPPING_FILE)
        self.form_mapping = self._load_json(settings.FORM_MAPPING_FILE)
        self.examples = self._load_json(settings.EXAMPLES_FILE)
        self.inv_form_mapping = self._create_inverse_form_mapping()
        self.inv_examples_mapping = self._create_inverse_examples_mapping()
        self.llm_client = OpenAI(
            base_url=settings.OPENAI_API_BASE_URL,
            api_key=settings.OPENAI_API_KEY
        )
        logger.info("SRL Analyzer initialized successfully")

    def _load_json(self, filename: str | Path) -> dict:
        """Load and parse a JSON file."""
        logger.debug(f"Loading JSON file: {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data

    def _create_inverse_form_mapping(self) -> Dict[str, str]:
        """Create inverse mapping from lemmatized forms to predicate groups."""
        inv_mapping = {}
        for group, forms in self.form_mapping.items():
            lemmas = [self._lemmatize(f) for f in forms]
            for lemma in lemmas:
                inv_mapping[lemma] = group
        return inv_mapping

    def _create_inverse_examples_mapping(self) -> Dict[str, List[dict]]:
        """Create inverse mapping from groups to examples."""
        inv_mapping = {}
        for ex in self.examples:
            group = ex['group']
            if group not in inv_mapping:
                inv_mapping[group] = []
            inv_mapping[group].append(ex)
        return inv_mapping

    def _lemmatize(self, word: str) -> str:
        """Lemmatize a single word using spaCy."""
        return next(iter(self.nlp(word))).lemma_

    def find_verbs(self, text: str) -> Tuple[List[str], List[str]]:
        """Find verbs in text and return their lemmas and original forms."""
        verbs, forms = [], []
        for tok in self.nlp(text):
            if tok.pos_ == "VERB":
                verbs.append(tok.lemma_)
                forms.append(tok.text)
        return verbs, forms

    def has_relevant_predicates(self, text: str) -> bool:
        """Check if text contains any relevant predicates."""
        lemmas, _ = self.find_verbs(text)
        return bool(set(lemmas).intersection(self.inv_form_mapping.keys()))

    def extract_predicates(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract relevant predicates and their lemmas from text."""
        lemmas, forms = self.find_verbs(text)
        new_lemmas, new_forms = [], []
        for lemma, form in zip(lemmas, forms):
            if lemma in self.inv_form_mapping:
                new_lemmas.append(lemma)
                new_forms.append(form)
        return new_forms, new_lemmas

    def get_predicate_group(self, lemmas: List[str]) -> Optional[str]:
        """Get predicate group for given lemmas."""
        for lemma in lemmas:
            if lemma in self.inv_form_mapping:
                return self.inv_form_mapping[lemma]
        return None

    def make_prompt(self, text: str, predicate_group: str) -> List[dict]:
        """Create prompt for LLM based on text and predicate group."""
        # Get role definitions for this predicate group
        rule_set = self.role_mapping[predicate_group]
        rule_set = json.dumps(rule_set, ensure_ascii=False, indent=4)
        example_set = self.inv_examples_mapping[predicate_group][:2]  # Use only 2 examples for clarity

        # Start with system message explaining the task and rules
        prompt = [
            {
                'role': 'system',
                'content': f'''You are a Russian linguist specializing in semantic role labeling.
Your task is to analyze Russian text and identify semantic roles according to these rules:

{rule_set}

Format your response as a JSON object with a "roles" array. Each role should have:
- short_reasoning: Brief explanation of why this role was assigned
- arg_role: The semantic role from the rules above
- arg_phrase_or_clause: The full phrase or clause that fills this role
- arg_main_indicative_word: The main word that indicates this role

If no roles can be identified, return a single role with "Not-Applicable" values.'''
            }
        ]

        # Add examples
        for ex in example_set:
            # Format example text
            example_text = ex['text']
            prompt.append({
                'role': 'user',
                'content': example_text
            })

            # Format example roles
            roles = []
            for role in ex['roles']:
                if '#predicate' not in role['entity']:
                    role_parts = role['entity'].split('#')
                    roles.append({
                        'short_reasoning': 'Example role from training data',
                        'arg_role': role_parts[1],
                        'arg_phrase_or_clause': role_parts[0].strip('- '),
                        'arg_main_indicative_word': role_parts[0].strip('- ').split()[0]
                    })
            
            prompt.append({
                'role': 'assistant',
                'content': json.dumps({'roles': roles}, ensure_ascii=False, indent=2)
            })

        # Add the actual text to analyze
        prompt.append({
            'role': 'user',
            'content': f'''Please analyze this text and identify all semantic roles:
{text}

Remember:
1. Only identify roles that are explicitly present in the text
2. Use the exact words/phrases from the input text
3. Provide clear, concise reasoning for each role
4. If no roles can be identified, use "Not-Applicable"'''
        })

        return prompt

    async def analyze(self, text: str) -> dict:
        """Analyze text and extract semantic roles."""
        logger.info(f"Analyzing text: {text}")
        
        if not self.has_relevant_predicates(text):
            logger.info("No relevant predicates found")
            return {
                "text": text,
                "predicates": [],
                "lemmas": [],
                "roles": [],
                "has_relevant_predicates": False
            }

        predicates, lemmas = self.extract_predicates(text)
        logger.info(f"Found predicates: {predicates}, lemmas: {lemmas}")
        
        predicate_group = self.inv_form_mapping[lemmas[0]]
        logger.debug(f"Using predicate group: {predicate_group}")
        
        prompt = self.make_prompt(text, predicate_group)
        logger.debug(f"Generated prompt: {json.dumps(prompt, ensure_ascii=False, indent=2)}")

        try:
            logger.debug("Making LLM API call")
            response = self.llm_client.chat.completions.create(
                model=settings.OPENAI_MODEL_NAME,
                messages=prompt,
                max_completion_tokens=1024,
                temperature=0.0,
                extra_body={
                    "guided_json": SemanticRoleMarkup.model_json_schema()
                },
            )
            
            roles_text = response.choices[0].message.content
            logger.debug(f"Raw roles text from LLM:\n{roles_text}")
            
            try:
                parsed_json = json.loads(roles_text)
                llm_roles = parsed_json['roles']
                
                # Convert LLM roles to simplified API format
                roles = []
                for role in llm_roles:
                    # Extract the actual phrase from the explanation
                    text = role['text']
                    # Find the phrase in parentheses
                    start_idx = text.find('(')
                    end_idx = text.find(')')
                    if start_idx != -1 and end_idx != -1:
                        parentheses_content = text[start_idx + 1:end_idx]
                        # For Experiencer, take the first word
                        # For other roles, take the last word before the closing parenthesis
                        if role['role'] == 'Experiencer':
                            phrase = parentheses_content.split()[0]
                        else:
                            phrase = parentheses_content.split()[-1]
                            
                        roles.append({
                            'role': role['role'],
                            'text': phrase
                        })
                        logger.debug(f"Added role: {json.dumps({'role': role['role'], 'text': phrase}, ensure_ascii=False)}")
                
                logger.info(f"Extracted roles: {json.dumps(roles, ensure_ascii=False)}")
            except Exception as e:
                logger.error(f"Error during role conversion: {e}")
                roles = []
            
            result = {
                "text": text,
                "predicates": predicates,
                "lemmas": lemmas,
                "roles": roles,
                "has_relevant_predicates": True
            }
            return result
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            return {
                "text": text,
                "predicates": predicates,
                "lemmas": lemmas,
                "roles": [],
                "has_relevant_predicates": True,
                "error": str(e)
            } 