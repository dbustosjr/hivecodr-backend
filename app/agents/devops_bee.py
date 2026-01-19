"""DevOps Bee agent - generates deployment configurations and manages cloud deployments."""

from crewai import Agent, Task
from typing import Dict, Any, Optional
from app.core.config import settings
from langchain_anthropic import ChatAnthropic
import json
import os


class DevOpsBeeAgent:
    """
    DevOps Bee agent that generates deployment configurations and optionally
    deploys applications to Railway (backend) and Vercel (frontend).

    This agent creates production-ready deployment files including Dockerfile,
    docker-compose.yml, railway.json, vercel.json, and environment templates.
    """

    def __init__(self):
        """Initialize the DevOps Bee agent."""
        self.model = ChatAnthropic(
            model=settings.CLAUDE_MODEL,
            anthropic_api_key=settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.7,
            max_tokens=4096
        )

    def _create_agent(self) -> Agent:
        """
        Creates the DevOps Bee agent with CrewAI.

        Returns:
            Agent: Configured CrewAI agent for DevOps automation
        """
        return Agent(
            role="Senior DevOps Engineer",
            goal="Generate production-ready deployment configurations and optionally deploy to cloud platforms",
            backstory=(
                "You are an expert DevOps engineer with deep expertise in containerization, "
                "cloud deployments, CI/CD pipelines, and infrastructure as code. You excel at "
                "creating secure, scalable deployment configurations for Railway and Vercel. "
                "You understand Docker best practices, environment variable management, "
                "health checks, and zero-downtime deployments. You always follow the 12-factor "
                "app methodology and ensure configurations are production-ready."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.model
        )

    def _create_task(
        self,
        agent: Agent,
        app_name: str,
        architecture: Dict[str, Any],
        backend_files: Dict[str, str],
        frontend_files: Dict[str, str]
    ) -> Task:
        """
        Creates a CrewAI task for generating deployment configurations.

        Args:
            agent: The DevOps Bee agent
            app_name: Application name (URL-safe)
            architecture: Architecture spec from Architect Bee
            backend_files: Generated backend files
            frontend_files: Generated frontend files

        Returns:
            Task: Configured CrewAI task for deployment config generation
        """
        # Get list of backend dependencies
        backend_deps = []
        if "requirements.txt" in backend_files:
            backend_deps = backend_files["requirements.txt"].split("\n")

        task_description = f"""
Generate complete deployment configurations for the application: {app_name}

ARCHITECTURE OVERVIEW:
{json.dumps(architecture, indent=2)[:1000]}...

BACKEND FILES GENERATED:
{list(backend_files.keys())[:20]}

FRONTEND FILES GENERATED:
{list(frontend_files.keys())[:20]}

You must generate ALL deployment configuration files in JSON format. Be PRECISE and production-ready.

REQUIRED OUTPUT FORMAT:
{{
    "deployment_files": {{
        "Dockerfile": "<<< COMPLETE Dockerfile content for Python FastAPI backend >>>",
        "start.sh": "<<< COMPLETE startup script with PORT handling >>>",
        "docker-compose.yml": "<<< COMPLETE docker-compose for local dev >>>",
        "railway.json": "<<< COMPLETE Railway deployment config >>>",
        "vercel.json": "<<< COMPLETE Vercel frontend config >>>",
        ".env.example": "<<< COMPLETE environment variables template >>>",
        "README.md": "<<< COMPLETE deployment instructions >>>"
    }},
    "environment_variables": {{
        "backend": {{
            "VARIABLE_NAME": {{
                "required": true or false,
                "description": "What this variable does",
                "default": "default_value or null",
                "example": "example_value"
            }}
        }},
        "frontend": {{
            "NEXT_PUBLIC_API_URL": {{
                "required": true,
                "description": "Backend API URL",
                "default": null,
                "example": "https://my-app.railway.app"
            }}
        }}
    }},
    "deployment_instructions": {{
        "manual_deployment": {{
            "railway_steps": ["Step 1", "Step 2", "Step 3"],
            "vercel_steps": ["Step 1", "Step 2", "Step 3"]
        }},
        "prerequisites": ["What user needs before deploying"],
        "estimated_time": "15-20 minutes"
    }}
}}

CRITICAL REQUIREMENTS:

1. Dockerfile:
   - Use python:3.13-slim base image
   - Install gcc for dependencies
   - Copy requirements.txt and install packages
   - Copy all application files
   - Make start.sh executable
   - EXPOSE 8000
   - CMD ["./start.sh"]

2. start.sh (MUST USE THIS EXACT PATTERN):
   ```bash
   #!/bin/bash
   set -e
   PORT=${{PORT:-8000}}
   echo "Starting uvicorn on port $PORT"
   exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
   ```

3. railway.json:
   - Use DOCKERFILE builder
   - startCommand: "./start.sh"
   - healthcheckPath: "/health"
   - healthcheckTimeout: 100
   - restartPolicyType: "ON_FAILURE"
   - restartPolicyMaxRetries: 10

4. vercel.json:
   - Configure Next.js build
   - Set output directory
   - Configure rewrites if needed

5. .env.example:
   - List ALL required environment variables
   - Include descriptions and example values
   - Separate backend and frontend variables clearly
   - Include: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, SUPABASE_JWT_SECRET
   - Include: DATABASE_URL if using PostgreSQL

6. docker-compose.yml:
   - Backend service with build context
   - PostgreSQL service (if needed based on architecture)
   - Frontend service (if running locally)
   - Volume mounts for development
   - Environment variables from .env file

7. README.md:
   - Project overview
   - Prerequisites (Node.js, Python, Railway account, Vercel account)
   - Local development setup
   - Manual deployment instructions for Railway
   - Manual deployment instructions for Vercel
   - Environment variables reference
   - Troubleshooting common issues

IMPORTANT:
- All file contents must be COMPLETE and ready to use
- No placeholders or TODOs
- Follow best practices for security (no hardcoded secrets)
- Include proper error handling in scripts
- Add health check endpoints
- Configure CORS properly
- Use production-grade settings
"""

        expected_output = """
Complete JSON object with all deployment files and configurations.
All files must be production-ready with no placeholders.
"""

        return Task(
            description=task_description,
            expected_output=expected_output,
            agent=agent
        )

    def generate_deployment_configs(
        self,
        app_name: str,
        architecture: Dict[str, Any],
        backend_files: Dict[str, str],
        frontend_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generates deployment configurations for the application.

        Args:
            app_name: Application name (URL-safe)
            architecture: Architecture specification
            backend_files: Generated backend code files
            frontend_files: Generated frontend code files

        Returns:
            Dict containing deployment files and configurations
        """
        from crewai import Crew

        # Create agent and task
        agent = self._create_agent()
        task = self._create_task(
            agent=agent,
            app_name=app_name,
            architecture=architecture,
            backend_files=backend_files,
            frontend_files=frontend_files
        )

        # Execute the task
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()

        # Parse the result
        try:
            if hasattr(result, 'raw'):
                result_text = result.raw
            else:
                result_text = str(result)

            # Try to extract JSON from the result
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()

            deployment_config = json.loads(result_text)
            return deployment_config

        except json.JSONDecodeError as e:
            print(f"Error parsing DevOps Bee output: {e}")
            print(f"Raw output: {result_text[:500]}")
            # Return minimal deployment config as fallback
            return self._generate_fallback_config(app_name, backend_files, frontend_files)

    def _generate_fallback_config(
        self,
        app_name: str,
        backend_files: Dict[str, str],
        frontend_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Generates a basic deployment configuration as fallback.

        Args:
            app_name: Application name
            backend_files: Backend code files
            frontend_files: Frontend code files

        Returns:
            Basic deployment configuration
        """
        return {
            "deployment_files": {
                "Dockerfile": self._get_default_dockerfile(),
                "start.sh": self._get_default_start_script(),
                "railway.json": self._get_default_railway_config(),
                ".env.example": self._get_default_env_example(),
                "README.md": f"# {app_name}\n\nDeployment instructions coming soon."
            },
            "environment_variables": {
                "backend": {
                    "ANTHROPIC_API_KEY": {
                        "required": True,
                        "description": "Anthropic API key for Claude",
                        "default": None,
                        "example": "sk-ant-xxxxx"
                    }
                },
                "frontend": {
                    "NEXT_PUBLIC_API_URL": {
                        "required": True,
                        "description": "Backend API URL",
                        "default": None,
                        "example": f"https://{app_name}.railway.app"
                    }
                }
            },
            "deployment_instructions": {
                "manual_deployment": {
                    "railway_steps": [
                        "Push code to GitHub",
                        "Create new Railway project",
                        "Connect GitHub repository",
                        "Add environment variables",
                        "Deploy"
                    ],
                    "vercel_steps": [
                        "Push code to GitHub",
                        "Import project in Vercel",
                        "Configure build settings",
                        "Add environment variables",
                        "Deploy"
                    ]
                },
                "prerequisites": [
                    "GitHub account",
                    "Railway account",
                    "Vercel account"
                ],
                "estimated_time": "15-20 minutes"
            }
        }

    def _get_default_dockerfile(self) -> str:
        """Returns default Dockerfile content."""
        return """FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
"""

    def _get_default_start_script(self) -> str:
        """Returns default start.sh content."""
        return """#!/bin/bash
set -e

PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
"""

    def _get_default_railway_config(self) -> str:
        """Returns default railway.json content."""
        return """{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "./start.sh",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
"""

    def _get_default_env_example(self) -> str:
        """Returns default .env.example content."""
        return """# API Keys
ANTHROPIC_API_KEY=sk-ant-your_key_here

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Application
ENVIRONMENT=production
MAX_DAILY_COST=100
RATE_LIMIT_GENERATIONS=10
RATE_LIMIT_WINDOW=3600

# Claude API
CLAUDE_MODEL=claude-sonnet-4-20250514
"""
