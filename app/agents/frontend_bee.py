"""Frontend Bee agent that generates Next.js 14 frontend code based on FastAPI backend."""

from crewai import Agent, Task, Crew
from typing import Dict, Any
from pathlib import Path
from app.core.complexity_analyzer import complexity_analyzer
from langchain_anthropic import ChatAnthropic
import json
import os
import time
import httpx
from app.core.config import settings


class FrontendBeeAgent:
    """Frontend Bee agent that generates Next.js 14 applications with TypeScript and Tailwind CSS."""

    def __init__(self):
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
        self.model = ChatAnthropic(
            model=settings.CLAUDE_MODEL,
            temperature=0.7,
            max_tokens=4096,
            timeout=120.0,  # 2 minutes for Railway network latency
            max_retries=3,
            http_client=http_client  # Use HTTP/2 client
        )

    def _create_agent(self) -> Agent:
        """Create the Frontend Bee agent with specialized frontend development skills."""
        return Agent(
            role="Senior Frontend Developer (Next.js & TypeScript Specialist)",
            goal="Generate production-ready Next.js 14 applications with TypeScript, Tailwind CSS, and complete CRUD functionality based on FastAPI backend specifications",
            backstory="""You are an expert frontend developer specializing in Next.js 14, TypeScript, and modern React patterns.

You have deep knowledge of:
- Next.js 14 App Router and server components
- TypeScript for type safety
- Tailwind CSS for responsive, mobile-first design
- React Hook Form for form validation
- API integration with fetch and error handling
- Accessibility best practices
- Component composition and reusability

You create clean, maintainable code following Next.js and React best practices. Your generated applications are:
- Fully typed with TypeScript
- Responsive and mobile-first
- Accessible (WCAG 2.1 compliant)
- Well-structured with proper component organization
- Include proper error handling and loading states
- Use modern React patterns (hooks, composition)
- Follow the Single Responsibility Principle

You always generate COMPLETE, working code - never placeholders or TODOs.""",
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )

    def _create_task(self, agent: Agent, backend_code: Dict[str, str], requirements: str, architecture_spec: Dict[str, Any]) -> Task:
        """
        Create the frontend generation task.

        Args:
            agent: The Frontend Bee agent
            backend_code: Generated backend code (models, schemas, routes, main)
            requirements: Original user requirements
            architecture_spec: Architecture specification from Architect Bee

        Returns:
            Task for generating Next.js frontend
        """
        # Extract entities from architecture spec
        entities = []
        if architecture_spec and "database_schema" in architecture_spec:
            tables = architecture_spec["database_schema"].get("tables", [])
            entities = [table["name"] for table in tables]

        entities_str = ", ".join(entities) if entities else "the main entities"

        task_description = f"""Generate a complete Next.js 14 application with TypeScript and Tailwind CSS based on the FastAPI backend.

**Original Requirements:**
{requirements}

**Backend Entities:**
{entities_str}

**Backend Code Structure:**
The backend has the following files:
- models.py: SQLAlchemy models
- schemas.py: Pydantic schemas
- routes.py: FastAPI routes
- main.py: Application setup

**Your Task:**
Generate a COMPLETE Next.js 14 frontend application with the following structure:

1. **Project Configuration Files:**
   - package.json (with all dependencies)
   - tsconfig.json (TypeScript configuration)
   - tailwind.config.ts (with HiveCodr color palette)
   - next.config.js (Next.js configuration)
   - .env.local (environment variables)

2. **Application Structure:**
   - app/layout.tsx (root layout with navigation)
   - app/page.tsx (home page)
   - app/globals.css (Tailwind CSS with HiveCodr colors)

3. **For EACH entity in the backend, create:**
   - app/[entity]/page.tsx (list view with pagination)
   - app/[entity]/[id]/page.tsx (detail view)
   - app/[entity]/new/page.tsx (create form)
   - app/[entity]/[id]/edit/page.tsx (edit form)
   - components/[entity]/[Entity]List.tsx (list component)
   - components/[entity]/[Entity]Card.tsx (card component)
   - components/[entity]/[Entity]Form.tsx (form component)
   - lib/api/[entity].ts (API functions)
   - lib/types/[entity].ts (TypeScript types)

4. **Shared Components:**
   - components/ui/Button.tsx
   - components/ui/Input.tsx
   - components/ui/Card.tsx
   - components/ui/Loading.tsx
   - components/ui/Error.tsx
   - components/layout/Navigation.tsx
   - components/layout/Footer.tsx

5. **Utilities:**
   - lib/api/client.ts (API client with error handling)
   - lib/utils.ts (utility functions)
   - lib/validations.ts (form validation schemas)

**HiveCodr Color Palette (use in Tailwind config):**
- Primary: #220901 (Dark Brown)
- Secondary: #621708 (Brown)
- Accent: #941B0C (Red)
- Highlight: #BC3908 (Orange)
- Accent Gold: #F6AA1C (Yellow/Gold)

**Requirements:**
1. Use Next.js 14 App Router (not Pages Router)
2. Use TypeScript for all files
3. Use Tailwind CSS for styling with HiveCodr colors
4. Implement proper error handling and loading states
5. Make it responsive and mobile-first
6. Use React Hook Form for forms with validation
7. Include proper TypeScript types for all API responses
8. Add proper error messages and success notifications
9. Include search, filter, and pagination where appropriate
10. Make all components accessible (proper ARIA labels, keyboard navigation)

**Important:**
- Generate COMPLETE, working code for ALL files
- Do NOT use placeholders, TODOs, or "implement this"
- Every component must be fully functional
- All API calls must have proper error handling
- All forms must have validation
- The app must be production-ready

**Output Format:**
Return a JSON object with this exact structure:
{{
  "package.json": "complete file content",
  "tsconfig.json": "complete file content",
  "tailwind.config.ts": "complete file content",
  "next.config.js": "complete file content",
  ".env.local": "complete file content",
  "app/layout.tsx": "complete file content",
  "app/page.tsx": "complete file content",
  "app/globals.css": "complete file content",
  "components/ui/Button.tsx": "complete file content",
  "components/ui/Input.tsx": "complete file content",
  "components/ui/Card.tsx": "complete file content",
  "components/ui/Loading.tsx": "complete file content",
  "components/ui/Error.tsx": "complete file content",
  "components/layout/Navigation.tsx": "complete file content",
  "components/layout/Footer.tsx": "complete file content",
  "lib/api/client.ts": "complete file content",
  "lib/utils.ts": "complete file content",
  "lib/validations.ts": "complete file content",
  ... (include ALL entity-specific files)
}}

Generate production-ready, complete code for every single file. Make it beautiful, functional, and follow Next.js 14 best practices."""

        return Task(
            description=task_description,
            agent=agent,
            expected_output="A complete JSON object containing all Next.js 14 application files with TypeScript, Tailwind CSS, and full CRUD functionality for all entities"
        )

    def generate_frontend_code_with_retry(
        self,
        backend_code: Dict[str, str],
        requirements: str,
        architecture_spec: Dict[str, Any],
        output_dir: str = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Generate Next.js 14 frontend code with intelligent retry logic.

        Args:
            backend_code: Generated backend code
            requirements: User requirements
            architecture_spec: Architecture specification
            output_dir: Output directory
            max_attempts: Maximum retry attempts

        Returns:
            Dict containing file paths, metadata, and retry information
        """
        attempts = []
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"\n{'='*60}")
                print(f"Frontend Bee - Attempt {attempt}/{max_attempts}")
                print(f"{'='*60}")

                # Determine strategy for this attempt
                if attempt == 1:
                    attempt_type = "Full frontend with all features"
                elif attempt == 2:
                    attempt_type = "Simplified frontend (basic components only)"
                    print(f"RETRY STRATEGY: {attempt_type}")
                else:
                    attempt_type = "Minimal frontend (essential pages only)"
                    print(f"RETRY STRATEGY: {attempt_type}")

                # Attempt generation
                result = self.generate_frontend_code(
                    backend_code,
                    requirements,
                    architecture_spec,
                    output_dir
                )

                # Success! Add retry info
                result["retry_info"] = {
                    "attempts": attempt,
                    "final_attempt_type": attempt_type,
                    "attempt_history": attempts + [{
                        "attempt": attempt,
                        "type": attempt_type,
                        "status": "success"
                    }]
                }

                print(f"\n[SUCCESS] Frontend Bee succeeded on attempt {attempt}")
                return result

            except Exception as e:
                last_error = str(e)
                attempts.append({
                    "attempt": attempt,
                    "type": attempt_type if 'attempt_type' in locals() else "Full frontend",
                    "status": "failed",
                    "error": str(e)[:200]
                })

                print(f"\n[FAILED] Attempt {attempt} failed: {str(e)[:100]}")

                if attempt < max_attempts:
                    print(f"[RETRY] Retrying with simplified approach...")
                    time.sleep(2)
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

    def generate_frontend_code(
        self,
        backend_code: Dict[str, str],
        requirements: str,
        architecture_spec: Dict[str, Any],
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        Generate Next.js 14 frontend code based on backend.

        Args:
            backend_code: Generated backend code (models, schemas, routes, main)
            output_dir: Directory where frontend files should be written
            requirements: Original user requirements
            architecture_spec: Architecture specification from Architect Bee

        Returns:
            Dictionary containing frontend code files and metadata
        """
        agent = self._create_agent()
        task = self._create_task(agent, backend_code, requirements, architecture_spec)

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )

        print(f"Frontend Bee generating Next.js application...")
        result = crew.kickoff()

        # Parse the result to extract frontend code
        frontend_code = self._parse_frontend_output(str(result))

        # Write files to output directory if provided
        if output_dir:
            frontend_dir = Path(output_dir) / "frontend"
            frontend_dir.mkdir(parents=True, exist_ok=True)

            file_paths = {}
            file_stats = {}

            for file_path, content in frontend_code.items():
                if content:  # Only write non-empty files
                    # Create nested directories if needed (e.g., app/, components/)
                    full_path = frontend_dir / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content, encoding='utf-8')
                    file_paths[file_path] = str(full_path)
                    file_stats[file_path] = {
                        "lines": len(content.split('\n')),
                        "chars": len(content),
                        "path": str(full_path)
                    }

            return {
                "file_paths": file_paths,
                "file_stats": file_stats,
                "output_dir": str(frontend_dir),
                "agent_log": str(result),
                "files_written": len(file_paths)
            }
        else:
            # Legacy behavior: return code content
            return {
                "code": frontend_code,
                "agent_log": str(result),
                "raw_response": str(result)
            }

    def _parse_frontend_output(self, output: str) -> Dict[str, str]:
        """
        Parse the frontend code output from the agent.

        Args:
            output: Raw output from the agent

        Returns:
            Dictionary of file paths to file contents
        """
        try:
            # Try to find JSON in the output
            start_idx = output.find('{')
            end_idx = output.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = output[start_idx:end_idx]

                # Try parsing as-is first
                try:
                    frontend_files = json.loads(json_str)
                    return frontend_files
                except json.JSONDecodeError:
                    # Try using json-repair library for malformed JSON
                    try:
                        from json_repair import repair_json
                        repaired = repair_json(json_str)
                        frontend_files = json.loads(repaired)
                        return frontend_files
                    except Exception:
                        # If repair fails, fall through to fallback
                        pass

            # Fallback: return as single file
            return {
                "app/page.tsx": output,
                "README.md": "# Frontend Generation\n\nFrontend code generated successfully. See app/page.tsx for the main application."
            }
        except Exception:
            # If JSON parsing fails completely, return the output as-is
            return {
                "output.txt": output,
                "README.md": "# Frontend Generation\n\nNote: Output could not be parsed as JSON. See output.txt for raw output."
            }


# Create a singleton instance
frontend_bee = FrontendBeeAgent()
