"""Architect Bee agent - analyzes requirements and creates technical specifications."""

from crewai import Agent, Task
from typing import Dict, Any
from app.core.config import settings
from langchain_anthropic import ChatAnthropic
import json
import os
import httpx

# Monkey-patch httpx.Client to always use HTTP/2 for Railway compatibility
_original_httpx_client_init = httpx.Client.__init__

def _patched_httpx_client_init(self, **kwargs):
    """Patched httpx.Client.__init__ that forces HTTP/2."""
    if 'http2' not in kwargs:
        kwargs['http2'] = True
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 120.0
    _original_httpx_client_init(self, **kwargs)

httpx.Client.__init__ = _patched_httpx_client_init


class ArchitectBeeAgent:
    """
    Architect Bee agent that analyzes requirements and creates technical specifications.

    This agent designs the database schema, API structure, and validation rules
    before code generation begins.
    """

    def __init__(self):
        """Initialize the Architect Bee agent."""
        # HTTP/2 is enabled globally via monkey-patch above
        # Let ChatAnthropic auto-detect ANTHROPIC_API_KEY from environment
        self.model = ChatAnthropic(
            model=settings.CLAUDE_MODEL,
            temperature=0.7,
            max_tokens=4096,
            timeout=120.0,  # 2 minutes for Railway network latency
            max_retries=3
        )

    def _create_agent(self) -> Agent:
        """
        Creates the Architect Bee agent with CrewAI.

        Returns:
            Agent: Configured CrewAI agent for architecture design
        """
        return Agent(
            role="Senior Software Architect",
            goal="Analyze requirements and design robust database schemas and API structures",
            backstory=(
                "You are an expert software architect specializing in RESTful API design "
                "and database modeling. You excel at translating business requirements into "
                "well-structured technical specifications. You consider data relationships, "
                "scalability, security, and best practices in every design decision."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )

    def _create_task(self, agent: Agent, requirements: str) -> Task:
        """
        Creates a CrewAI task for architecture design.

        Args:
            agent: The Architect Bee agent
            requirements: User's plain English requirements

        Returns:
            Task: Configured CrewAI task for architecture
        """
        task_description = f"""
Analyze the following requirements and create a CONCISE technical specification:

REQUIREMENTS:
{requirements}

You must provide a architecture specification in JSON format. Be CONCISE - keep descriptions brief (1-2 sentences max).
Use this structure:

{{
    "database_schema": {{
        "tables": [
            {{
                "name": "table_name",
                "description": "What this table stores",
                "fields": [
                    {{
                        "name": "field_name",
                        "type": "SQLAlchemy type (Integer, String, Text, Boolean, DateTime, etc.)",
                        "constraints": ["primary_key", "nullable", "unique", "index", etc.],
                        "description": "What this field represents",
                        "max_length": 200  // Only for String types
                    }}
                ],
                "relationships": [
                    {{
                        "type": "one_to_many" or "many_to_one" or "many_to_many",
                        "target_table": "related_table_name",
                        "description": "Relationship description"
                    }}
                ]
            }}
        ]
    }},
    "api_endpoints": [
        {{
            "method": "POST" or "GET" or "PUT" or "DELETE",
            "path": "/api/v1/resource",
            "description": "What this endpoint does",
            "request_body": {{
                "field_name": {{
                    "type": "str" or "int" or "bool" or "datetime",
                    "required": true or false,
                    "description": "Field description"
                }}
            }},
            "response": {{
                "status_code": 200,
                "description": "Response description"
            }},
            "query_parameters": [
                {{
                    "name": "param_name",
                    "type": "str" or "int" or "bool",
                    "required": false,
                    "default": "default_value",
                    "description": "Parameter description"
                }}
            ]
        }}
    ],
    "validation_rules": {{
        "entity_name": [
            {{
                "field": "field_name",
                "rules": ["min_length: 1", "max_length: 200", "pattern: regex", etc.],
                "error_message": "Validation error message"
            }}
        ]
    }},
    "business_logic": [
        "Key business rule 1",
        "Key business rule 2"
    ]
}}

IMPORTANT:
1. Be CONCISE - short descriptions only
2. Include only essential fields
3. Use standard RESTful endpoints (GET, POST, PUT, DELETE)
4. Include timestamps (created_at, updated_at) for main entities
5. Keep validation_rules minimal or omit if not critical

Return ONLY valid JSON, no markdown code blocks, no additional text. Ensure proper JSON syntax with commas between all array/object elements.
"""

        return Task(
            description=task_description,
            agent=agent,
            expected_output="JSON specification with database schema, API endpoints, and validation rules"
        )

    def _parse_architecture_json(self, result_text: str) -> Dict[str, Any]:
        """
        Parse architecture JSON from LLM output with robust error handling.

        Tries multiple strategies to extract and fix JSON:
        1. Extract from markdown code blocks
        2. Find JSON object directly
        3. Fix common JSON syntax errors
        4. Truncate if too long

        Args:
            result_text: Raw output from LLM

        Returns:
            Parsed JSON as dictionary

        Raises:
            Exception: If all parsing strategies fail
        """
        import re

        # Strategy 1: Try to extract from markdown code blocks
        json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_block_pattern, result_text, re.DOTALL)
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        # Strategy 2: Find JSON object directly
        start_idx = result_text.find("{")
        end_idx = result_text.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON object found in response")

        json_str = result_text[start_idx:end_idx]

        # Strategy 3: Try parsing as-is
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Strategy 4: Use json-repair library (designed for LLM JSON)
            try:
                from json_repair import repair_json
                repaired = repair_json(json_str)
                return json.loads(repaired)
            except Exception as repair_error:
                # Strategy 5: Try to fix common JSON errors manually
                fixed_json = self._fix_common_json_errors(json_str, e)
                try:
                    return json.loads(fixed_json)
                except json.JSONDecodeError:
                    # Strategy 6: If JSON is too long and truncated, try to close it properly
                    if len(json_str) > 15000:  # Very long JSON, likely truncated
                        fixed_json = self._close_truncated_json(json_str)
                        try:
                            return json.loads(fixed_json)
                        except json.JSONDecodeError:
                            pass

                    # All strategies failed
                    raise Exception(
                        f"Failed to parse JSON after trying all strategies. "
                        f"Original error: {str(e)}. "
                        f"JSON repair error: {str(repair_error)}. "
                        f"JSON length: {len(json_str)}. "
                        f"First 500 chars: {json_str[:500]}"
                    )

    def _fix_common_json_errors(self, json_str: str, error: json.JSONDecodeError) -> str:
        """
        Attempt to fix common JSON syntax errors.

        Args:
            json_str: Malformed JSON string
            error: The JSONDecodeError that occurred

        Returns:
            Potentially fixed JSON string
        """
        import re

        # Remove any trailing commas before closing braces/brackets
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Remove any duplicate commas
        json_str = re.sub(r',\s*,', ',', json_str)

        # Fix missing commas between adjacent objects/arrays
        # Pattern: }{ or ]{ or }[ or ]{
        json_str = re.sub(r'\}(\s*)\{', r'},\1{', json_str)
        json_str = re.sub(r'\](\s*)\{', r'],\1{', json_str)
        json_str = re.sub(r'\}(\s*)\[', r'},\1[', json_str)
        json_str = re.sub(r'\](\s*)\[', r'],\1[', json_str)

        # Fix missing commas between string and brace/bracket
        # Pattern: "text"{ or "text"[
        json_str = re.sub(r'\"(\s*)\{', r'",\1{', json_str)
        json_str = re.sub(r'\"(\s*)\[', r'",\1[', json_str)

        # Fix missing commas between number and brace/bracket
        # Pattern: 123{ or 123[
        json_str = re.sub(r'(\d)(\s*)\{', r'\1,\2{', json_str)
        json_str = re.sub(r'(\d)(\s*)\[', r'\1,\2[', json_str)

        # Fix missing commas between boolean/null and brace/bracket
        json_str = re.sub(r'(true|false|null)(\s*)\{', r'\1,\2{', json_str)
        json_str = re.sub(r'(true|false|null)(\s*)\[', r'\1,\2[', json_str)

        return json_str

    def _close_truncated_json(self, json_str: str) -> str:
        """
        Attempt to properly close a truncated JSON object.

        Args:
            json_str: Truncated JSON string

        Returns:
            JSON string with added closing brackets
        """
        # Count opening and closing braces/brackets
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')

        # Add missing closing characters
        missing_braces = open_braces - close_braces
        missing_brackets = open_brackets - close_brackets

        # Remove any trailing comma that might be before our additions
        json_str = json_str.rstrip().rstrip(',')

        # Add closing brackets/braces in reverse order (arrays before objects)
        result = json_str
        result += ']' * missing_brackets
        result += '}' * missing_braces

        return result

    def analyze_requirements(self, requirements: str) -> Dict[str, Any]:
        """
        Analyzes requirements and creates technical specifications.

        Args:
            requirements: Plain English description of what to build

        Returns:
            Dict containing architecture specification

        Raises:
            Exception: If architecture design fails
        """
        try:
            # Create agent and task
            agent = self._create_agent()
            task = self._create_task(agent, requirements)

            # Execute the task directly
            from crewai import Crew

            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )

            # Execute the crew
            result = crew.kickoff()

            # Parse the result with robust error handling
            result_text = str(result)

            # Extract and parse JSON with multiple strategies
            architecture_spec = self._parse_architecture_json(result_text)

            # Validate that we have at least the database schema
            if "database_schema" not in architecture_spec:
                raise ValueError(f"Missing required key: database_schema")

            # Add defaults for optional/missing keys
            if "api_endpoints" not in architecture_spec:
                architecture_spec["api_endpoints"] = []
            if "validation_rules" not in architecture_spec:
                architecture_spec["validation_rules"] = {}
            if "business_logic" not in architecture_spec:
                architecture_spec["business_logic"] = []

            return {
                "specification": architecture_spec,
                "raw_output": result_text
            }

        except Exception as e:
            import traceback
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            print(f"[ERROR] Architecture analysis failed:")
            print(f"  Type: {error_details['error_type']}")
            print(f"  Message: {error_details['error_message']}")
            print(f"  Traceback: {error_details['traceback'][:1000]}")
            # Include error type in exception message for debugging
            raise Exception(f"Architecture analysis failed: [{error_details['error_type']}] {str(e)}")


# Global instance
architect_bee = ArchitectBeeAgent()
