"""Developer Bee agent - generates FastAPI CRUD code using CrewAI."""

from crewai import Agent, Task, Crew
from anthropic import Anthropic
from typing import Dict, Any, List
from app.core.config import settings
from app.core.complexity_analyzer import complexity_analyzer
from pathlib import Path
import json
import os
import time
import httpx


class DeveloperBeeAgent:
    """
    Developer Bee agent that generates complete FastAPI CRUD code.

    Uses CrewAI framework with Claude API to generate models, routes,
    and main.py based on plain English requirements.
    """

    def __init__(self):
        """Initialize the Developer Bee agent with Claude API."""
        # Create HTTP client with explicit HTTP/2 support for Railway
        http_client = httpx.Client(
            http2=True,
            timeout=120.0,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )

        # Increased timeout for Railway's slower network
        self.anthropic_client = Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            http_client=http_client,
            timeout=120.0,  # 2 minutes for Railway network latency
            max_retries=3
        )
        self.model = settings.CLAUDE_MODEL

    def _generate_files_chunked(self, architecture_spec: Dict[str, Any], requirements: str) -> Dict[str, str]:
        """
        Generate backend files separately for complex applications.

        Args:
            architecture_spec: Architecture specification
            requirements: User requirements

        Returns:
            Dict with keys: models, schemas, routes, main
        """
        print("[CHUNKED GENERATION] Generating files separately for reliability...")

        generated_files = {}
        spec_json = json.dumps(architecture_spec, indent=2)

        # 1. Generate models.py
        print("[CHUNKED] Step 1/4: Generating models.py...")
        try:
            models_prompt = f"""
Generate ONLY the models.py file for this FastAPI application.

ARCHITECTURE SPECIFICATION:
{spec_json}

REQUIREMENTS:
{requirements}

Create complete SQLAlchemy models with:
- All tables from the specification
- All fields with correct types and constraints
- All relationships (ForeignKey, relationship())
- Proper imports
- Docstrings for each model

Return ONLY the Python code for models.py, no JSON, no markdown, just the code.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": models_prompt}]
            )
            models_code = response.content[0].text.strip()

            # Clean up markdown if present
            if "```python" in models_code:
                models_code = models_code.split("```python")[1].split("```")[0].strip()
            elif "```" in models_code:
                models_code = models_code.split("```")[1].split("```")[0].strip()

            generated_files["models"] = models_code
            print(f"[CHUNKED] models.py: {len(models_code)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate models.py: {str(e)[:100]}")
            generated_files["models"] = "# Error generating models.py"

        # 2. Generate schemas.py
        print("[CHUNKED] Step 2/4: Generating schemas.py...")
        try:
            schemas_prompt = f"""
Generate ONLY the schemas.py file for this FastAPI application.

ARCHITECTURE SPECIFICATION:
{spec_json}

REQUIREMENTS:
{requirements}

Create complete Pydantic v2 schemas with:
- BaseModel classes for each model
- Validation rules from specification
- Proper field types
- Config class with orm_mode = True
- Create and Update variants

Return ONLY the Python code for schemas.py, no JSON, no markdown, just the code.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": schemas_prompt}]
            )
            schemas_code = response.content[0].text.strip()

            # Clean up markdown
            if "```python" in schemas_code:
                schemas_code = schemas_code.split("```python")[1].split("```")[0].strip()
            elif "```" in schemas_code:
                schemas_code = schemas_code.split("```")[1].split("```")[0].strip()

            generated_files["schemas"] = schemas_code
            print(f"[CHUNKED] schemas.py: {len(schemas_code)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate schemas.py: {str(e)[:100]}")
            generated_files["schemas"] = "# Error generating schemas.py"

        # 3. Generate routes.py
        print("[CHUNKED] Step 3/4: Generating routes.py...")
        try:
            routes_prompt = f"""
Generate ONLY the routes.py file for this FastAPI application.

ARCHITECTURE SPECIFICATION:
{spec_json}

REQUIREMENTS:
{requirements}

Create complete FastAPI routes with:
- APIRouter setup
- All CRUD endpoints (Create, Read, Update, Delete)
- Proper request/response schemas
- Error handling with HTTPException
- Database session management
- All endpoints from specification

Return ONLY the Python code for routes.py, no JSON, no markdown, just the code.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=10000,
                messages=[{"role": "user", "content": routes_prompt}]
            )
            routes_code = response.content[0].text.strip()

            # Clean up markdown
            if "```python" in routes_code:
                routes_code = routes_code.split("```python")[1].split("```")[0].strip()
            elif "```" in routes_code:
                routes_code = routes_code.split("```")[1].split("```")[0].strip()

            generated_files["routes"] = routes_code
            print(f"[CHUNKED] routes.py: {len(routes_code)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate routes.py: {str(e)[:100]}")
            generated_files["routes"] = "# Error generating routes.py"

        # 4. Generate main.py
        print("[CHUNKED] Step 4/4: Generating main.py...")
        try:
            main_prompt = f"""
Generate ONLY the main.py file for this FastAPI application.

Create a complete main.py with:
- FastAPI app initialization
- CORS middleware
- Router includes
- Database setup
- Application configuration
- Health check endpoint

Return ONLY the Python code for main.py, no JSON, no markdown, just the code.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": main_prompt}]
            )
            main_code = response.content[0].text.strip()

            # Clean up markdown
            if "```python" in main_code:
                main_code = main_code.split("```python")[1].split("```")[0].strip()
            elif "```" in main_code:
                main_code = main_code.split("```")[1].split("```")[0].strip()

            generated_files["main"] = main_code
            print(f"[CHUNKED] main.py: {len(main_code)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate main.py: {str(e)[:100]}")
            generated_files["main"] = "# Error generating main.py"

        print(f"[CHUNKED GENERATION] Complete. Generated {len([f for f in generated_files.values() if f and not f.startswith('# Error')])} files successfully.")

        return generated_files

    def _create_agent(self) -> Agent:
        """
        Creates the Developer Bee agent with CrewAI.

        Returns:
            Agent: Configured CrewAI agent
        """
        return Agent(
            role="Senior FastAPI Developer",
            goal="Generate production-ready FastAPI CRUD code based on requirements",
            backstory=(
                "You are an expert Python developer specializing in FastAPI. "
                "You create clean, well-structured CRUD applications with proper "
                "models, routes, and error handling. You follow best practices "
                "and write secure, maintainable code."
            ),
            verbose=False  # Disabled to reduce Railway log volume,
            allow_delegation=False,
            llm=self.model
        )

    def _create_task(self, agent: Agent, requirements: str, architecture_spec: Dict[str, Any] = None) -> Task:
        """
        Creates a CrewAI task for code generation.

        Args:
            agent: The Developer Bee agent
            requirements: User's plain English requirements
            architecture_spec: Optional architecture specification from Architect Bee

        Returns:
            Task: Configured CrewAI task
        """
        if architecture_spec:
            # Generate code based on architecture specification
            spec_json = json.dumps(architecture_spec, indent=2)
            task_description = f"""
Generate complete FastAPI CRUD code based on this architecture specification:

ORIGINAL REQUIREMENTS:
{requirements}

ARCHITECTURE SPECIFICATION:
{spec_json}

You must implement the specification exactly as designed and provide:
1. SQLAlchemy models (models.py) - Implement all tables with fields, types, and relationships as specified
2. Pydantic schemas (schemas.py) - Create schemas for validation matching the specification
3. API routes (routes.py) - Implement all endpoints with the specified methods, paths, and parameters
4. Main application file (main.py) - FastAPI app setup with CORS, error handling, and database initialization

Requirements:
- Follow the architecture specification precisely
- Use SQLAlchemy ORM for database models with the exact field types specified
- Use Pydantic v2 for schemas with all validation rules from the specification
- Implement all API endpoints as designed
- Include proper error handling with HTTPException
- Add comprehensive docstrings
- Follow FastAPI best practices
- Use async/await where appropriate
- Include proper HTTP status codes

Return the code as a JSON object with keys: models, schemas, routes, main
Each value should be the complete file content as a string.
"""
        else:
            # Fallback to requirements-based generation
            task_description = f"""
Generate complete FastAPI CRUD code based on these requirements:

{requirements}

You must provide:
1. SQLAlchemy models (models.py) with proper relationships
2. Pydantic schemas (schemas.py) for request/response validation
3. API routes (routes.py) with full CRUD operations (Create, Read, Update, Delete)
4. Main application file (main.py) that ties everything together

Requirements:
- Use SQLAlchemy ORM for database models
- Use Pydantic v2 for schemas
- Include proper error handling with HTTPException
- Add input validation
- Include docstrings
- Follow FastAPI best practices
- Use async/await where appropriate
- Include proper status codes

Return the code as a JSON object with keys: models, schemas, routes, main
Each value should be the complete file content as a string.
"""

        return Task(
            description=task_description,
            agent=agent,
            expected_output="JSON object containing models, schemas, routes, and main files"
        )

    def generate_crud_code_with_retry(
        self,
        requirements: str,
        architecture_spec: Dict[str, Any] = None,
        output_dir: str = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Generates FastAPI CRUD code with intelligent retry logic.

        Args:
            requirements: Plain English description of what to build
            architecture_spec: Optional architecture specification from Architect Bee
            output_dir: Directory where generated files should be written
            max_attempts: Maximum number of retry attempts

        Returns:
            Dict containing file paths, metadata, execution log, and retry information
        """
        attempts = []
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"\n{'='*60}")
                print(f"Developer Bee - Attempt {attempt}/{max_attempts}")
                print(f"{'='*60}")

                # Determine requirements for this attempt
                if attempt == 1:
                    # First attempt: use original requirements
                    current_requirements = requirements
                    attempt_type = "Full requirements"
                elif attempt == 2:
                    # Second attempt: simplified requirements
                    current_requirements = complexity_analyzer.create_simplified_requirements(
                        requirements, simplification_level=1
                    )
                    attempt_type = "Simplified (remove advanced features)"
                    print(f"RETRY STRATEGY: {attempt_type}")
                else:
                    # Third attempt: minimal CRUD
                    current_requirements = complexity_analyzer.create_simplified_requirements(
                        requirements, simplification_level=3
                    )
                    attempt_type = "Minimal (core CRUD only)"
                    print(f"RETRY STRATEGY: {attempt_type}")

                # Attempt generation
                result = self.generate_crud_code(
                    current_requirements,
                    architecture_spec,
                    output_dir
                )

                # Success! Add attempt info and return
                result["retry_info"] = {
                    "attempts": attempt,
                    "final_attempt_type": attempt_type,
                    "attempt_history": attempts + [{
                        "attempt": attempt,
                        "type": attempt_type,
                        "status": "success"
                    }]
                }

                print(f"\n[SUCCESS] Developer Bee succeeded on attempt {attempt}")
                return result

            except Exception as e:
                last_error = str(e)
                attempts.append({
                    "attempt": attempt,
                    "type": attempt_type if 'attempt_type' in locals() else "Full requirements",
                    "status": "failed",
                    "error": str(e)[:200]  # Truncate error message
                })

                print(f"\n[FAILED] Attempt {attempt} failed: {str(e)[:100]}")

                if attempt < max_attempts:
                    print(f"[RETRY] Retrying with simplified requirements...")
                    time.sleep(2)  # Brief pause before retry
                else:
                    print(f"\n[FAILED] All {max_attempts} attempts failed")

        # All attempts failed - return graceful degradation
        return {
            "file_paths": {},
            "file_stats": {},
            "output_dir": output_dir if output_dir else "N/A",
            "agent_log": f"All {max_attempts} attempts failed. Last error: {last_error}",
            "files_written": 0,
            "retry_info": {
                "attempts": max_attempts,
                "final_attempt_type": "all_failed",
                "attempt_history": attempts,
                "last_error": last_error
            },
            "status": "failed"
        }

    def generate_crud_code(self, requirements: str, architecture_spec: Dict[str, Any] = None, output_dir: str = None) -> Dict[str, Any]:
        """
        Generates FastAPI CRUD code based on requirements and optional architecture spec.

        Args:
            requirements: Plain English description of what to build
            architecture_spec: Optional architecture specification from Architect Bee
            output_dir: Directory where generated files should be written

        Returns:
            Dict containing file paths, metadata, and execution log

        Raises:
            Exception: If code generation fails
        """
        print("="*80)
        print("DEVELOPER BEE - GENERATE_CRUD_CODE CALLED")
        print("="*80)

        try:
            # Create agent and task
            agent = self._create_agent()
            task = self._create_task(agent, requirements, architecture_spec)

            # Create crew and execute
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False  # Disabled to reduce Railway log volume
            )

            # Execute the crew
            result = crew.kickoff()

            # Parse the result
            agent_log = str(result)

            # Prepare the prompt for Claude
            if architecture_spec:
                spec_json = json.dumps(architecture_spec, indent=2)
                claude_prompt = f"""
Generate complete FastAPI CRUD code based on this architecture specification:

ARCHITECTURE SPECIFICATION:
{spec_json}

ORIGINAL REQUIREMENTS:
{requirements}

Provide 4 files implementing the specification:
1. models.py - SQLAlchemy models with all tables, fields, and relationships as specified
2. schemas.py - Pydantic schemas with validation rules from the specification
3. routes.py - FastAPI routes implementing all API endpoints as designed
4. main.py - Main FastAPI application with setup and configuration

Return ONLY a valid JSON object in this exact format:
{{
    "models": "# models.py content here",
    "schemas": "# schemas.py content here",
    "routes": "# routes.py content here",
    "main": "# main.py content here"
}}

Make the code production-ready with error handling, validation, and docstrings.
Follow the architecture specification precisely.
"""
            else:
                claude_prompt = f"""
Generate complete FastAPI CRUD code for: {requirements}

Provide 4 files:
1. models.py - SQLAlchemy models
2. schemas.py - Pydantic schemas
3. routes.py - FastAPI routes with CRUD operations
4. main.py - Main FastAPI application

Return ONLY a valid JSON object in this exact format:
{{
    "models": "# models.py content here",
    "schemas": "# schemas.py content here",
    "routes": "# routes.py content here",
    "main": "# main.py content here"
}}

Make the code production-ready with error handling, validation, and docstrings.
"""

            # Determine if we should use chunked generation
            table_count = len(architecture_spec.get('database_schema', {}).get('tables', [])) if architecture_spec else 1
            use_chunked_generation = table_count > 4  # Use chunks for complex apps

            print(f"Table count: {table_count}")
            print(f"Using {'CHUNKED' if use_chunked_generation else 'SINGLE'} generation strategy")

            if use_chunked_generation:
                # Generate each file separately for better reliability
                generated_code = self._generate_files_chunked(architecture_spec, requirements)
            else:
                # Generate all files at once (works well for simple apps)
                # Use Claude API directly with increased token limit
                response = self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=16000,  # Increased from 4096 for complex apps
                    messages=[
                        {
                            "role": "user",
                            "content": claude_prompt
                        }
                    ]
                )

                # Extract the generated code
                code_text = response.content[0].text

                print(f"[DEBUG] Received {len(code_text)} characters from Claude API")

                # Try to parse JSON from the response
                try:
                    # Find JSON object in response
                    start_idx = code_text.find("{")
                    end_idx = code_text.rfind("}") + 1
                    json_str = code_text[start_idx:end_idx]

                    print(f"[DEBUG] Extracted JSON string: {len(json_str)} characters")

                    # Try json-repair for malformed JSON
                    try:
                        generated_code = json.loads(json_str)
                        print(f"[DEBUG] Successfully parsed JSON with {len(generated_code)} keys")
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] JSON parse failed: {str(e)[:100]}, trying json-repair...")
                        from json_repair import repair_json
                        repaired = repair_json(json_str)
                        generated_code = json.loads(repaired)
                        print(f"[DEBUG] json-repair succeeded")
                except (json.JSONDecodeError, ValueError, Exception) as e:
                    print(f"[ERROR] All JSON parsing strategies failed: {str(e)[:200]}")
                    # Fallback: create structured response
                    generated_code = {
                        "models": code_text,
                        "schemas": "",
                        "routes": "",
                        "main": ""
                    }

            # Ensure generated_code is a dictionary
            if not isinstance(generated_code, dict):
                print(f"[WARNING] generated_code is not a dict, converting...")
                generated_code = {
                    "models": str(generated_code),
                    "schemas": "",
                    "routes": "",
                    "main": ""
                }

            # Log what we got
            for filename, content in generated_code.items():
                content_len = len(content) if content else 0
                print(f"[DEBUG] {filename}: {content_len} characters")

            # Write files to output directory if provided
            if output_dir:
                backend_dir = Path(output_dir) / "backend"
                backend_dir.mkdir(parents=True, exist_ok=True)

                file_paths = {}
                file_stats = {}

                for filename, content in generated_code.items():
                    if content:  # Only write non-empty files
                        file_path = backend_dir / f"{filename}.py"
                        file_path.write_text(content, encoding='utf-8')
                        file_paths[filename] = str(file_path)
                        file_stats[filename] = {
                            "lines": len(content.split('\n')),
                            "chars": len(content),
                            "path": str(file_path)
                        }

                return {
                    "file_paths": file_paths,
                    "file_stats": file_stats,
                    "output_dir": str(backend_dir),
                    "agent_log": agent_log,
                    "files_written": len(file_paths)
                }
            else:
                # Legacy behavior: return code content
                return {
                    "code": generated_code,
                    "agent_log": agent_log,
                    "raw_response": code_text
                }

        except Exception as e:
            raise Exception(f"Code generation failed: {str(e)}")


# Global instance
developer_bee = DeveloperBeeAgent()
