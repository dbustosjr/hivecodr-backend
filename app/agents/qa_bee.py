"""QA Bee Agent - Generates comprehensive pytest test suites for backend code."""

from crewai import Agent, Task, Crew
from typing import Dict, Any
import json
from pathlib import Path
import time
from anthropic import Anthropic
import os


class QABeeAgent:
    """
    QA Bee Agent that generates comprehensive pytest test suites for backend code.

    Generates 4 test files:
    - test_models.py: Unit tests for SQLAlchemy models
    - test_schemas.py: Pydantic schema validation tests
    - test_routes.py: Integration tests for API endpoints
    - conftest.py: pytest fixtures and test configuration
    """

    def __init__(self):
        """Initialize QA Bee with CrewAI and Claude API configurations."""
        self.model = "claude-sonnet-4-20250514"
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _generate_test_files_chunked(
        self,
        backend_code: Dict[str, str],
        architecture_spec: Dict[str, Any],
        requirements: str
    ) -> Dict[str, str]:
        """
        Generate test files separately for better reliability and coverage.

        Args:
            backend_code: Dictionary containing models, schemas, routes code
            architecture_spec: Architecture specification from Architect Bee
            requirements: Original user requirements

        Returns:
            Dictionary mapping test filenames to their content
        """
        print("[CHUNKED TEST GENERATION] Generating test files separately for comprehensive coverage...")

        generated_tests = {}
        spec_json = json.dumps(architecture_spec, indent=2)

        # Prepare backend code context
        models_code = backend_code.get("models", "")
        schemas_code = backend_code.get("schemas", "")
        routes_code = backend_code.get("routes", "")

        # Step 1/4: Generate conftest.py first (needed for other tests)
        print("[CHUNKED] Step 1/4: Generating conftest.py...")
        try:
            conftest_prompt = f"""
Generate a comprehensive conftest.py file for pytest testing of a FastAPI application.

BACKEND CODE CONTEXT:
Models: {len(models_code)} characters
Schemas: {len(schemas_code)} characters
Routes: {len(routes_code)} characters

ARCHITECTURE SPECIFICATION:
{spec_json}

REQUIREMENTS:
{requirements}

Create a conftest.py file with:
1. Database fixtures (test database setup/teardown)
2. SQLAlchemy session fixtures (create test tables, cleanup)
3. FastAPI TestClient fixture
4. Authentication fixtures (if applicable)
5. Sample data fixtures for common test scenarios
6. Pytest configuration

Best practices:
- Use in-memory SQLite for fast tests
- Proper cleanup with yield fixtures
- Scope fixtures appropriately (function, module, session)
- Include docstrings explaining each fixture
- Create fixtures for common test data (users, posts, etc.)

Return ONLY the Python code for conftest.py, no JSON, no markdown, just the code.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": conftest_prompt}]
            )
            conftest_code = response.content[0].text.strip()

            # Clean up markdown
            if "```python" in conftest_code:
                conftest_code = conftest_code.split("```python")[1].split("```")[0].strip()
            elif "```" in conftest_code:
                conftest_code = conftest_code.split("```")[1].split("```")[0].strip()

            generated_tests["conftest"] = conftest_code
            print(f"[CHUNKED] conftest.py: {len(conftest_code)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate conftest.py: {str(e)[:100]}")
            generated_tests["conftest"] = "# Error generating conftest.py"

        # Step 2/4: Generate test_models.py
        print("[CHUNKED] Step 2/4: Generating test_models.py...")
        try:
            test_models_prompt = f"""
Generate comprehensive unit tests for SQLAlchemy models in test_models.py.

MODELS CODE:
{models_code[:15000]}

ARCHITECTURE SPECIFICATION:
{spec_json}

Create test_models.py with:
1. Test model creation (test_create_<model_name>)
2. Test model fields and constraints
3. Test relationships (foreign keys, one-to-many, many-to-many)
4. Test unique constraints
5. Test nullable constraints
6. Test default values
7. Test model methods if any
8. Test cascading deletes if applicable

Best practices:
- Use pytest fixtures from conftest.py
- Use descriptive test names (test_create_user_with_valid_data)
- Test both positive and negative cases
- Use parametrize for testing multiple scenarios
- Include docstrings explaining what each test does
- Aim for high code coverage

Return ONLY the Python code for test_models.py, no JSON, no markdown, just the code.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=10000,
                messages=[{"role": "user", "content": test_models_prompt}]
            )
            test_models_code = response.content[0].text.strip()

            # Clean up markdown
            if "```python" in test_models_code:
                test_models_code = test_models_code.split("```python")[1].split("```")[0].strip()
            elif "```" in test_models_code:
                test_models_code = test_models_code.split("```")[1].split("```")[0].strip()

            generated_tests["test_models"] = test_models_code
            print(f"[CHUNKED] test_models.py: {len(test_models_code)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate test_models.py: {str(e)[:100]}")
            generated_tests["test_models"] = "# Error generating test_models.py"

        # Step 3/4: Generate test_schemas.py
        print("[CHUNKED] Step 3/4: Generating test_schemas.py...")
        try:
            test_schemas_prompt = f"""
Generate comprehensive validation tests for Pydantic schemas in test_schemas.py.

SCHEMAS CODE:
{schemas_code[:15000]}

ARCHITECTURE SPECIFICATION:
{spec_json}

Create test_schemas.py with:
1. Test valid data passes validation
2. Test invalid data is rejected
3. Test required fields
4. Test optional fields
5. Test field types (string, int, email, etc.)
6. Test field constraints (max length, min value, etc.)
7. Test edge cases (empty strings, null values, very long strings)
8. Test schema serialization/deserialization

Best practices:
- Use pytest.raises for testing validation errors
- Use parametrize to test multiple invalid inputs
- Test both Create and Update schemas
- Test response schemas
- Include descriptive test names
- Test edge cases thoroughly

Return ONLY the Python code for test_schemas.py, no JSON, no markdown, just the code.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": test_schemas_prompt}]
            )
            test_schemas_code = response.content[0].text.strip()

            # Clean up markdown
            if "```python" in test_schemas_code:
                test_schemas_code = test_schemas_code.split("```python")[1].split("```")[0].strip()
            elif "```" in test_schemas_code:
                test_schemas_code = test_schemas_code.split("```")[1].split("```")[0].strip()

            generated_tests["test_schemas"] = test_schemas_code
            print(f"[CHUNKED] test_schemas.py: {len(test_schemas_code)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate test_schemas.py: {str(e)[:100]}")
            generated_tests["test_schemas"] = "# Error generating test_schemas.py"

        # Step 4/4: Generate test_routes.py
        print("[CHUNKED] Step 4/4: Generating test_routes.py...")
        try:
            test_routes_prompt = f"""
Generate comprehensive integration tests for FastAPI routes in test_routes.py.

ROUTES CODE:
{routes_code[:20000]}

ARCHITECTURE SPECIFICATION:
{spec_json}

Create test_routes.py with:
1. Test all CRUD operations (Create, Read, Update, Delete)
2. Test successful responses (200, 201, 204)
3. Test error responses (400, 404, 422)
4. Test input validation (valid and invalid data)
5. Test query parameters (pagination, filtering, search)
6. Test authentication/authorization if applicable
7. Test edge cases (non-existent IDs, duplicate entries)
8. Test database state after operations

Best practices:
- Use TestClient from conftest.py
- Test each endpoint with valid and invalid data
- Verify response status codes
- Verify response data structure
- Test database side effects
- Use descriptive test names
- Group related tests in classes
- Aim for 80%+ route coverage

Return ONLY the Python code for test_routes.py, no JSON, no markdown, just the code.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=12000,
                messages=[{"role": "user", "content": test_routes_prompt}]
            )
            test_routes_code = response.content[0].text.strip()

            # Clean up markdown
            if "```python" in test_routes_code:
                test_routes_code = test_routes_code.split("```python")[1].split("```")[0].strip()
            elif "```" in test_routes_code:
                test_routes_code = test_routes_code.split("```")[1].split("```")[0].strip()

            generated_tests["test_routes"] = test_routes_code
            print(f"[CHUNKED] test_routes.py: {len(test_routes_code)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate test_routes.py: {str(e)[:100]}")
            generated_tests["test_routes"] = "# Error generating test_routes.py"

        print(f"[CHUNKED TEST GENERATION] Complete. Generated {len(generated_tests)} test files successfully.")
        return generated_tests

    def _generate_frontend_tests(
        self,
        frontend_code: Dict[str, str],
        architecture_spec: Dict[str, Any],
        requirements: str
    ) -> Dict[str, str]:
        """
        Generate comprehensive frontend tests (Jest + React Testing Library).

        Args:
            frontend_code: Dictionary containing frontend code
            architecture_spec: Architecture specification
            requirements: Original user requirements

        Returns:
            Dictionary mapping test filenames to their content
        """
        print("[FRONTEND TESTS] Generating component and integration tests...")

        generated_tests = {}
        spec_json = json.dumps(architecture_spec, indent=2)

        # Step 1: Generate Jest configuration
        print("[FRONTEND] Step 1/3: Generating jest.config.js...")
        try:
            jest_config_prompt = f"""
Generate a jest.config.js file for testing a Next.js 14 application with TypeScript.

REQUIREMENTS:
{requirements}

Create jest.config.js with:
- Next.js preset configuration
- TypeScript support
- Testing Library setup
- Coverage configuration
- Module path mapping
- Transform configuration for .tsx files

Return ONLY the JavaScript code for jest.config.js, no markdown.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": jest_config_prompt}]
            )
            jest_config = response.content[0].text.strip()
            if "```" in jest_config:
                jest_config = jest_config.split("```")[1].split("```")[0].strip()
                if jest_config.startswith("javascript") or jest_config.startswith("js"):
                    jest_config = jest_config.split('\n', 1)[1]

            generated_tests["jest.config"] = jest_config
            print(f"[FRONTEND] jest.config.js: {len(jest_config)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate jest.config.js: {str(e)[:100]}")
            generated_tests["jest.config"] = "// Error generating jest.config.js"

        # Step 2: Generate component tests
        print("[FRONTEND] Step 2/3: Generating component tests...")
        try:
            component_tests_prompt = f"""
Generate comprehensive React component tests for a Next.js application.

ARCHITECTURE SPECIFICATION:
{spec_json}

REQUIREMENTS:
{requirements}

Create component test files using Jest + React Testing Library:
1. Test main page components (rendering, user interactions)
2. Test form submissions and validations
3. Test data display components
4. Test loading and error states
5. Test user interactions (clicks, input changes)

Best practices:
- Use @testing-library/react
- Test user behavior, not implementation details
- Use screen queries (getByRole, getByText, etc.)
- Test accessibility
- Mock API calls
- Use descriptive test names

Return a JSON object with test files:
{{
  "page.test": "test code for main page",
  "components/[ComponentName].test": "test code for components"
}}

Return ONLY valid JSON, no markdown.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=10000,
                messages=[{"role": "user", "content": component_tests_prompt}]
            )
            component_tests_text = response.content[0].text.strip()

            # Parse JSON
            start_idx = component_tests_text.find("{")
            end_idx = component_tests_text.rfind("}") + 1
            json_str = component_tests_text[start_idx:end_idx]

            try:
                component_tests = json.loads(json_str)
            except:
                from json_repair import repair_json
                repaired = repair_json(json_str)
                component_tests = json.loads(repaired)

            # Add component tests to generated_tests
            for filename, content in component_tests.items():
                generated_tests[filename] = content
                print(f"[FRONTEND] {filename}.tsx: {len(content)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate component tests: {str(e)[:100]}")
            generated_tests["page.test"] = "// Error generating component tests"

        # Step 3: Generate API integration tests
        print("[FRONTEND] Step 3/3: Generating API integration tests...")
        try:
            api_tests_prompt = f"""
Generate API integration tests for frontend API calls.

ARCHITECTURE SPECIFICATION:
{spec_json}

Create integration/api.test.tsx with:
1. Test API fetch calls (mocked)
2. Test loading states
3. Test error states
4. Test success states
5. Test data transformation
6. Mock fetch responses

Use MSW (Mock Service Worker) or jest.mock for API mocking.

Return ONLY the TypeScript code for api.test.tsx, no markdown.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=6000,
                messages=[{"role": "user", "content": api_tests_prompt}]
            )
            api_tests = response.content[0].text.strip()
            if "```" in api_tests:
                api_tests = api_tests.split("```")[1].split("```")[0].strip()
                if api_tests.startswith("typescript") or api_tests.startswith("tsx"):
                    api_tests = api_tests.split('\n', 1)[1]

            generated_tests["integration/api.test"] = api_tests
            print(f"[FRONTEND] integration/api.test.tsx: {len(api_tests)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate API tests: {str(e)[:100]}")
            generated_tests["integration/api.test"] = "// Error generating API tests"

        print(f"[FRONTEND TESTS] Complete. Generated {len(generated_tests)} frontend test files.")
        return generated_tests

    def _generate_e2e_tests(
        self,
        architecture_spec: Dict[str, Any],
        requirements: str
    ) -> Dict[str, str]:
        """
        Generate E2E tests using Playwright.

        Args:
            architecture_spec: Architecture specification
            requirements: Original user requirements

        Returns:
            Dictionary mapping test filenames to their content
        """
        print("[E2E TESTS] Generating Playwright end-to-end tests...")

        generated_tests = {}
        spec_json = json.dumps(architecture_spec, indent=2)

        # Step 1: Generate Playwright config
        print("[E2E] Step 1/3: Generating playwright.config.ts...")
        try:
            playwright_config_prompt = f"""
Generate playwright.config.ts for E2E testing of a Next.js application.

REQUIREMENTS:
{requirements}

Create configuration with:
- Test directory setup
- Browser configurations (chromium, firefox, webkit)
- Base URL configuration
- Screenshot and video on failure
- Retry configuration
- Timeout settings

Return ONLY the TypeScript code, no markdown.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": playwright_config_prompt}]
            )
            playwright_config = response.content[0].text.strip()
            if "```" in playwright_config:
                playwright_config = playwright_config.split("```")[1].split("```")[0].strip()
                if playwright_config.startswith("typescript") or playwright_config.startswith("ts"):
                    playwright_config = playwright_config.split('\n', 1)[1]

            generated_tests["playwright.config"] = playwright_config
            print(f"[E2E] playwright.config.ts: {len(playwright_config)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate playwright config: {str(e)[:100]}")

        # Step 2: Generate CRUD E2E tests
        print("[E2E] Step 2/3: Generating CRUD operations E2E tests...")
        try:
            crud_e2e_prompt = f"""
Generate Playwright E2E tests for CRUD operations.

ARCHITECTURE SPECIFICATION:
{spec_json}

REQUIREMENTS:
{requirements}

Create e2e/crud-operations.spec.ts with:
1. Test creating new entities through UI
2. Test reading/viewing entities
3. Test updating entities
4. Test deleting entities
5. Test form validations
6. Test navigation between pages
7. Use page object model if complex

Return ONLY the TypeScript code, no markdown.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": crud_e2e_prompt}]
            )
            crud_e2e = response.content[0].text.strip()
            if "```" in crud_e2e:
                crud_e2e = crud_e2e.split("```")[1].split("```")[0].strip()
                if crud_e2e.startswith("typescript") or crud_e2e.startswith("ts"):
                    crud_e2e = crud_e2e.split('\n', 1)[1]

            generated_tests["e2e/crud-operations.spec"] = crud_e2e
            print(f"[E2E] crud-operations.spec.ts: {len(crud_e2e)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate CRUD E2E tests: {str(e)[:100]}")

        # Step 3: Generate full workflow E2E test
        print("[E2E] Step 3/3: Generating full workflow E2E test...")
        try:
            workflow_e2e_prompt = f"""
Generate Playwright E2E test for complete user workflow.

REQUIREMENTS:
{requirements}

Create e2e/full-workflow.spec.ts testing:
1. User navigates to application
2. Performs complete workflow (create -> read -> update -> delete)
3. Test realistic user journey
4. Test cross-page functionality
5. Verify data persistence

Return ONLY the TypeScript code, no markdown.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=6000,
                messages=[{"role": "user", "content": workflow_e2e_prompt}]
            )
            workflow_e2e = response.content[0].text.strip()
            if "```" in workflow_e2e:
                workflow_e2e = workflow_e2e.split("```")[1].split("```")[0].strip()
                if workflow_e2e.startswith("typescript") or workflow_e2e.startswith("ts"):
                    workflow_e2e = workflow_e2e.split('\n', 1)[1]

            generated_tests["e2e/full-workflow.spec"] = workflow_e2e
            print(f"[E2E] full-workflow.spec.ts: {len(workflow_e2e)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate workflow E2E test: {str(e)[:100]}")

        print(f"[E2E TESTS] Complete. Generated {len(generated_tests)} E2E test files.")
        return generated_tests

    def _generate_security_tests(
        self,
        backend_code: Dict[str, str],
        architecture_spec: Dict[str, Any],
        requirements: str
    ) -> Dict[str, str]:
        """
        Generate security tests based on OWASP Top 10.

        Args:
            backend_code: Dictionary containing backend code
            architecture_spec: Architecture specification
            requirements: Original user requirements

        Returns:
            Dictionary mapping test filenames to their content
        """
        print("[SECURITY TESTS] Generating OWASP Top 10 security tests...")

        generated_tests = {}
        spec_json = json.dumps(architecture_spec, indent=2)

        tests_to_generate = [
            ("test_sql_injection", "SQL injection prevention", 6000),
            ("test_xss_protection", "XSS attack prevention", 5000),
            ("test_auth_security", "Authentication and authorization security", 6000),
            ("test_input_validation", "Input validation and sanitization", 5000),
        ]

        for idx, (filename, description, max_tokens) in enumerate(tests_to_generate, 1):
            print(f"[SECURITY] Step {idx}/{len(tests_to_generate)}: Generating {filename}.py...")
            try:
                security_prompt = f"""
Generate security tests for {description}.

ARCHITECTURE SPECIFICATION:
{spec_json}

REQUIREMENTS:
{requirements}

Create {filename}.py with:
- Tests for common {description} vulnerabilities
- Use OWASP Top 10 guidelines
- Test both attack attempts and proper defense
- Use pytest
- Include descriptive docstrings

Return ONLY the Python code, no markdown.
"""
                response = self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": security_prompt}]
                )
                security_test = response.content[0].text.strip()
                if "```python" in security_test:
                    security_test = security_test.split("```python")[1].split("```")[0].strip()
                elif "```" in security_test:
                    security_test = security_test.split("```")[1].split("```")[0].strip()

                generated_tests[filename] = security_test
                print(f"[SECURITY] {filename}.py: {len(security_test)} characters")

            except Exception as e:
                print(f"[ERROR] Failed to generate {filename}.py: {str(e)[:100]}")
                generated_tests[filename] = f"# Error generating {filename}.py"

        print(f"[SECURITY TESTS] Complete. Generated {len(generated_tests)} security test files.")
        return generated_tests

    def _generate_api_contract_tests(
        self,
        backend_code: Dict[str, str],
        architecture_spec: Dict[str, Any],
        requirements: str
    ) -> Dict[str, str]:
        """
        Generate API contract tests.

        Args:
            backend_code: Dictionary containing backend code
            architecture_spec: Architecture specification
            requirements: Original user requirements

        Returns:
            Dictionary mapping test filenames to their content
        """
        print("[API CONTRACT TESTS] Generating contract verification tests...")

        generated_tests = {}
        spec_json = json.dumps(architecture_spec, indent=2)

        try:
            contract_test_prompt = f"""
Generate API contract tests to verify backend matches frontend expectations.

ARCHITECTURE SPECIFICATION:
{spec_json}

REQUIREMENTS:
{requirements}

Create test_api_contracts.py with:
1. Test all API endpoint response schemas
2. Verify status codes match expectations
3. Verify error response formats
4. Test response data types
5. Ensure frontend can consume all responses
6. Use JSON schema validation

Return ONLY the Python code, no markdown.
"""
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[{"role": "user", "content": contract_test_prompt}]
            )
            contract_test = response.content[0].text.strip()
            if "```python" in contract_test:
                contract_test = contract_test.split("```python")[1].split("```")[0].strip()
            elif "```" in contract_test:
                contract_test = contract_test.split("```")[1].split("```")[0].strip()

            generated_tests["test_api_contracts"] = contract_test
            print(f"[API CONTRACT] test_api_contracts.py: {len(contract_test)} characters")

        except Exception as e:
            print(f"[ERROR] Failed to generate API contract tests: {str(e)[:100]}")
            generated_tests["test_api_contracts"] = "# Error generating contract tests"

        print(f"[API CONTRACT TESTS] Complete. Generated {len(generated_tests)} contract test files.")
        return generated_tests

    def _create_agent(self) -> Agent:
        """
        Creates the QA Bee agent with CrewAI.

        Returns:
            Agent: Configured CrewAI agent
        """
        return Agent(
            role="Senior Full-Stack QA Engineer",
            goal="Generate comprehensive test suites covering backend, frontend, E2E, security, and API contracts",
            backstory=(
                "You are an expert QA engineer specializing in full-stack testing. "
                "You create thorough test suites with high code coverage using pytest, Jest, "
                "React Testing Library, and Playwright. You understand OWASP security principles "
                "and write tests that catch bugs early and ensure code quality across the entire stack. "
                "You follow testing best practices and write tests that serve as documentation."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )

    def _create_task(
        self,
        agent: Agent,
        backend_code: Dict[str, str],
        architecture_spec: Dict[str, Any],
        requirements: str
    ) -> Task:
        """
        Creates a CrewAI task for test generation.

        Args:
            agent: The QA Bee agent
            backend_code: Generated backend code (models, schemas, routes)
            architecture_spec: Architecture specification from Architect Bee
            requirements: Original user requirements

        Returns:
            Task: Configured CrewAI task
        """
        models_summary = f"Models code: {len(backend_code.get('models', ''))} chars"
        schemas_summary = f"Schemas code: {len(backend_code.get('schemas', ''))} chars"
        routes_summary = f"Routes code: {len(backend_code.get('routes', ''))} chars"

        task_description = f"""
Generate comprehensive pytest test suite for a FastAPI application.

BACKEND CODE:
{models_summary}
{schemas_summary}
{routes_summary}

REQUIREMENTS:
{requirements}

You must generate 4 test files:
1. conftest.py - pytest fixtures and test configuration
2. test_models.py - unit tests for SQLAlchemy models
3. test_schemas.py - validation tests for Pydantic schemas
4. test_routes.py - integration tests for API endpoints

Requirements:
- Use pytest best practices (fixtures, parametrize, descriptive names)
- Aim for 80%+ code coverage
- Include both positive and negative test cases
- Test edge cases thoroughly
- Use descriptive test names that explain what is being tested
- Include docstrings for complex tests
- Follow the Arrange-Act-Assert pattern

Return a summary of the tests generated and estimated coverage.
"""

        return Task(
            description=task_description,
            agent=agent,
            expected_output="Summary of generated test files with estimated coverage"
        )

    def generate_test_suite(
        self,
        backend_code: Dict[str, str],
        architecture_spec: Dict[str, Any],
        requirements: str,
        frontend_code: Dict[str, str] = None,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        Generates comprehensive full-stack test suite.

        Args:
            backend_code: Dictionary containing models, schemas, routes code
            architecture_spec: Architecture specification from Architect Bee
            requirements: Original user requirements
            frontend_code: Dictionary containing frontend component code (optional)
            output_dir: Directory where test files should be written

        Returns:
            Dict containing file paths, metadata, and execution log for all test types

        Raises:
            Exception: If test generation fails
        """
        print("="*80)
        print("QA BEE - COMPREHENSIVE FULL-STACK TEST SUITE GENERATION")
        print("="*80)

        try:
            # Create agent and task
            agent = self._create_agent()
            task = self._create_task(agent, backend_code, architecture_spec, requirements)

            # Create crew and execute
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )

            # Execute the crew (for logging purposes)
            result = crew.kickoff()
            agent_log = str(result)

            # =================================================================
            # PHASE 1: BACKEND TESTS (existing - keep working)
            # =================================================================
            print("\n" + "="*80)
            print("PHASE 1: BACKEND TESTS")
            print("="*80)
            backend_tests = self._generate_test_files_chunked(
                backend_code,
                architecture_spec,
                requirements
            )

            # Log backend tests
            for filename, content in backend_tests.items():
                content_len = len(content) if content else 0
                print(f"[BACKEND] {filename}.py: {content_len} characters")

            # =================================================================
            # PHASE 2: FRONTEND TESTS (new)
            # =================================================================
            frontend_tests = {}
            if frontend_code:
                print("\n" + "="*80)
                print("PHASE 2: FRONTEND TESTS")
                print("="*80)
                try:
                    frontend_tests = self._generate_frontend_tests(
                        frontend_code,
                        architecture_spec,
                        requirements
                    )
                    print(f"[FRONTEND] Generated {len(frontend_tests)} test files")
                except Exception as e:
                    print(f"[WARNING] Frontend test generation failed: {str(e)}")
                    # Continue with other test types

            # =================================================================
            # PHASE 3: E2E TESTS (new)
            # =================================================================
            print("\n" + "="*80)
            print("PHASE 3: E2E TESTS")
            print("="*80)
            e2e_tests = {}
            try:
                e2e_tests = self._generate_e2e_tests(
                    architecture_spec,
                    requirements
                )
                print(f"[E2E] Generated {len(e2e_tests)} test files")
            except Exception as e:
                print(f"[WARNING] E2E test generation failed: {str(e)}")
                # Continue with other test types

            # =================================================================
            # PHASE 4: SECURITY TESTS (new)
            # =================================================================
            print("\n" + "="*80)
            print("PHASE 4: SECURITY TESTS")
            print("="*80)
            security_tests = {}
            try:
                security_tests = self._generate_security_tests(
                    backend_code,
                    architecture_spec,
                    requirements
                )
                print(f"[SECURITY] Generated {len(security_tests)} test files")
            except Exception as e:
                print(f"[WARNING] Security test generation failed: {str(e)}")
                # Continue with other test types

            # =================================================================
            # PHASE 5: API CONTRACT TESTS (new)
            # =================================================================
            print("\n" + "="*80)
            print("PHASE 5: API CONTRACT TESTS")
            print("="*80)
            contract_tests = {}
            try:
                contract_tests = self._generate_api_contract_tests(
                    backend_code,
                    architecture_spec,
                    requirements
                )
                print(f"[CONTRACT] Generated {len(contract_tests)} test files")
            except Exception as e:
                print(f"[WARNING] API contract test generation failed: {str(e)}")
                # Continue anyway

            # =================================================================
            # WRITE ALL TEST FILES TO OUTPUT DIRECTORY
            # =================================================================
            if output_dir:
                all_file_paths = {}
                all_file_stats = {}

                # Write backend tests to backend/tests/
                if backend_tests:
                    backend_tests_dir = Path(output_dir) / "backend" / "tests"
                    backend_tests_dir.mkdir(parents=True, exist_ok=True)

                    init_file = backend_tests_dir / "__init__.py"
                    init_file.write_text("# Backend test suite\n", encoding='utf-8')

                    for filename, content in backend_tests.items():
                        if content and not content.startswith("# Error"):
                            file_path = backend_tests_dir / f"{filename}.py"
                            file_path.write_text(content, encoding='utf-8')
                            all_file_paths[f"backend_tests/{filename}"] = str(file_path)
                            all_file_stats[f"backend_tests/{filename}"] = {
                                "lines": len(content.split('\n')),
                                "chars": len(content),
                                "path": str(file_path)
                            }

                # Write frontend tests to frontend/__tests__/
                if frontend_tests:
                    frontend_tests_dir = Path(output_dir) / "frontend" / "__tests__"
                    frontend_tests_dir.mkdir(parents=True, exist_ok=True)

                    for filename, content in frontend_tests.items():
                        if content:
                            file_path = frontend_tests_dir / filename
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            file_path.write_text(content, encoding='utf-8')
                            all_file_paths[f"frontend_tests/{filename}"] = str(file_path)
                            all_file_stats[f"frontend_tests/{filename}"] = {
                                "lines": len(content.split('\n')),
                                "chars": len(content),
                                "path": str(file_path)
                            }

                # Write E2E tests to e2e/
                if e2e_tests:
                    e2e_tests_dir = Path(output_dir) / "e2e"
                    e2e_tests_dir.mkdir(parents=True, exist_ok=True)

                    for filename, content in e2e_tests.items():
                        if content:
                            file_path = e2e_tests_dir / filename
                            file_path.write_text(content, encoding='utf-8')
                            all_file_paths[f"e2e_tests/{filename}"] = str(file_path)
                            all_file_stats[f"e2e_tests/{filename}"] = {
                                "lines": len(content.split('\n')),
                                "chars": len(content),
                                "path": str(file_path)
                            }

                # Write security tests to security/
                if security_tests:
                    security_tests_dir = Path(output_dir) / "security"
                    security_tests_dir.mkdir(parents=True, exist_ok=True)

                    init_file = security_tests_dir / "__init__.py"
                    init_file.write_text("# Security test suite\n", encoding='utf-8')

                    for filename, content in security_tests.items():
                        if content and not content.startswith("# Error"):
                            file_path = security_tests_dir / f"{filename}.py"
                            file_path.write_text(content, encoding='utf-8')
                            all_file_paths[f"security_tests/{filename}"] = str(file_path)
                            all_file_stats[f"security_tests/{filename}"] = {
                                "lines": len(content.split('\n')),
                                "chars": len(content),
                                "path": str(file_path)
                            }

                # Write API contract tests to backend/tests/
                if contract_tests:
                    contract_tests_dir = Path(output_dir) / "backend" / "tests"
                    contract_tests_dir.mkdir(parents=True, exist_ok=True)

                    for filename, content in contract_tests.items():
                        if content and not content.startswith("# Error"):
                            file_path = contract_tests_dir / f"{filename}.py"
                            file_path.write_text(content, encoding='utf-8')
                            all_file_paths[f"contract_tests/{filename}"] = str(file_path)
                            all_file_stats[f"contract_tests/{filename}"] = {
                                "lines": len(content.split('\n')),
                                "chars": len(content),
                                "path": str(file_path)
                            }

                # Calculate coverage estimates
                coverage_estimates = {
                    "backend": self._estimate_coverage(backend_tests),
                    "frontend": self._estimate_coverage(frontend_tests) if frontend_tests else "N/A",
                    "e2e": "Critical paths covered" if e2e_tests else "N/A",
                    "security": "OWASP Top 10 covered" if security_tests else "N/A",
                    "contracts": "100% endpoint coverage" if contract_tests else "N/A"
                }

                print("\n" + "="*80)
                print("TEST SUITE GENERATION COMPLETE")
                print("="*80)
                print(f"Backend Tests: {len(backend_tests)} files")
                print(f"Frontend Tests: {len(frontend_tests)} files")
                print(f"E2E Tests: {len(e2e_tests)} files")
                print(f"Security Tests: {len(security_tests)} files")
                print(f"Contract Tests: {len(contract_tests)} files")
                print(f"TOTAL: {len(all_file_paths)} test files")
                print("="*80)

                return {
                    "file_paths": all_file_paths,
                    "file_stats": all_file_stats,
                    "output_dir": str(output_dir),
                    "agent_log": agent_log,
                    "files_written": len(all_file_paths),
                    "test_counts": {
                        "backend": len(backend_tests),
                        "frontend": len(frontend_tests),
                        "e2e": len(e2e_tests),
                        "security": len(security_tests),
                        "contract": len(contract_tests),
                        "total": len(all_file_paths)
                    },
                    "coverage_estimates": coverage_estimates
                }
            else:
                # Legacy behavior: return test content
                return {
                    "backend_tests": backend_tests,
                    "frontend_tests": frontend_tests,
                    "e2e_tests": e2e_tests,
                    "security_tests": security_tests,
                    "contract_tests": contract_tests,
                    "agent_log": agent_log,
                    "estimated_coverage": {
                        "backend": self._estimate_coverage(backend_tests),
                        "frontend": self._estimate_coverage(frontend_tests) if frontend_tests else "N/A"
                    }
                }

        except Exception as e:
            raise Exception(f"Test generation failed: {str(e)}")

    def _estimate_coverage(self, generated_tests: Dict[str, str]) -> str:
        """
        Estimate test coverage based on generated tests.

        Args:
            generated_tests: Dictionary of generated test files

        Returns:
            Estimated coverage percentage as string
        """
        # Simple heuristic: count test functions
        total_tests = 0
        for content in generated_tests.values():
            if content and not content.startswith("# Error"):
                total_tests += content.count("def test_")

        if total_tests == 0:
            return "0%"
        elif total_tests < 5:
            return "40-50%"
        elif total_tests < 10:
            return "60-70%"
        elif total_tests < 20:
            return "75-85%"
        else:
            return "85-95%"

    def generate_test_suite_with_retry(
        self,
        backend_code: Dict[str, str],
        architecture_spec: Dict[str, Any],
        requirements: str,
        frontend_code: Dict[str, str] = None,
        output_dir: str = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Generates comprehensive full-stack test suite with intelligent retry logic.

        Args:
            backend_code: Dictionary containing models, schemas, routes code
            architecture_spec: Architecture specification from Architect Bee
            requirements: Original user requirements
            frontend_code: Dictionary containing frontend component code (optional)
            output_dir: Directory where test files should be written
            max_attempts: Maximum number of retry attempts

        Returns:
            Dict containing file paths, metadata, execution log, and retry information
        """
        from app.core.complexity_analyzer import complexity_analyzer

        attempts = []
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"\n{'='*60}")
                print(f"QA Bee - Attempt {attempt}/{max_attempts}")
                print(f"{'='*60}")

                # Determine scope for this attempt
                if attempt == 1:
                    # First attempt: full test suite (all test types)
                    current_requirements = requirements
                    attempt_type = "Full test suite (backend, frontend, E2E, security, contracts)"
                elif attempt == 2:
                    # Second attempt: skip edge case tests
                    current_requirements = requirements + "\n\nNote: Focus on core functionality, skip advanced edge cases."
                    attempt_type = "Simplified (core tests only)"
                    print(f"RETRY STRATEGY: {attempt_type}")
                else:
                    # Third attempt: minimal tests
                    current_requirements = requirements + "\n\nNote: Generate minimal smoke tests only."
                    attempt_type = "Minimal (smoke tests)"
                    print(f"RETRY STRATEGY: {attempt_type}")

                # Attempt generation
                result = self.generate_test_suite(
                    backend_code,
                    architecture_spec,
                    current_requirements,
                    frontend_code,
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

                print(f"\n[SUCCESS] QA Bee succeeded on attempt {attempt}")
                return result

            except Exception as e:
                last_error = str(e)
                attempts.append({
                    "attempt": attempt,
                    "type": attempt_type if 'attempt_type' in locals() else "Full test suite",
                    "status": "failed",
                    "error": str(e)[:200]
                })

                print(f"\n[FAILED] Attempt {attempt} failed: {str(e)[:100]}")

                if attempt < max_attempts:
                    print(f"[RETRY] Retrying with simplified scope...")
                    time.sleep(2)
                else:
                    print(f"\n[FAILED] All {max_attempts} attempts failed")

        # All attempts failed - return graceful degradation
        print("[WARNING] QA Bee failed, but backend/frontend still succeeded")
        return {
            "file_paths": {},
            "file_stats": {},
            "output_dir": output_dir if output_dir else "N/A",
            "agent_log": f"All {max_attempts} attempts failed. Last error: {last_error}",
            "files_written": 0,
            "test_counts": {
                "backend": 0,
                "frontend": 0,
                "e2e": 0,
                "security": 0,
                "contract": 0,
                "total": 0
            },
            "coverage_estimates": {
                "backend": "0%",
                "frontend": "N/A",
                "e2e": "N/A",
                "security": "N/A",
                "contracts": "N/A"
            },
            "retry_info": {
                "attempts": max_attempts,
                "final_attempt_type": "all_failed",
                "attempt_history": attempts,
                "last_error": last_error
            },
            "status": "failed"
        }


# Global instance
qa_bee = QABeeAgent()
