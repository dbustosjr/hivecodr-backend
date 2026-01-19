"""Railway deployment service for automated backend deployments."""

import requests
import time
import os
import tempfile
import zipfile
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RailwayDeploymentError(Exception):
    """Exception raised when Railway deployment fails."""
    pass


class RailwayDeployService:
    """
    Service for deploying applications to Railway using the API.

    Uses Railway GraphQL API for project creation and deployment.
    https://docs.railway.app/reference/public-api
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Railway deployment service.

        Args:
            api_token: Railway API token (if None, reads from environment)
        """
        self.api_token = api_token or os.getenv("RAILWAY_API_TOKEN")
        if not self.api_token:
            raise ValueError("RAILWAY_API_TOKEN not provided and not found in environment")

        self.api_url = "https://backboard.railway.app/graphql/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def _execute_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Railway API.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Response data

        Raises:
            RailwayDeploymentError: If the API request fails
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                error_msg = result["errors"][0].get("message", "Unknown error")
                raise RailwayDeploymentError(f"GraphQL error: {error_msg}")

            return result.get("data", {})

        except requests.RequestException as e:
            logger.error(f"Railway API request failed: {e}")
            raise RailwayDeploymentError(f"Failed to communicate with Railway API: {str(e)}")

    def create_project(self, project_name: str) -> Tuple[str, str]:
        """
        Create a new Railway project.

        Args:
            project_name: Name for the project

        Returns:
            Tuple of (project_id, environment_id)

        Raises:
            RailwayDeploymentError: If project creation fails
        """
        query = """
        mutation ProjectCreate($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                id
                name
                environments {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        }
        """

        variables = {
            "input": {
                "name": project_name
            }
        }

        try:
            data = self._execute_graphql(query, variables)
            project = data.get("projectCreate")

            if not project:
                raise RailwayDeploymentError("Failed to create project")

            project_id = project["id"]

            # Get production environment ID
            environments = project.get("environments", {}).get("edges", [])
            production_env = next(
                (env["node"] for env in environments if env["node"]["name"] == "production"),
                None
            )

            if not production_env:
                raise RailwayDeploymentError("Production environment not found")

            environment_id = production_env["id"]

            logger.info(f"Created Railway project: {project_name} ({project_id})")
            return project_id, environment_id

        except Exception as e:
            logger.error(f"Failed to create Railway project: {e}")
            raise RailwayDeploymentError(f"Project creation failed: {str(e)}")

    def create_service(
        self,
        project_id: str,
        environment_id: str,
        service_name: str,
        github_repo: Optional[str] = None
    ) -> str:
        """
        Create a service in the Railway project.

        Args:
            project_id: Railway project ID
            environment_id: Environment ID
            service_name: Name for the service
            github_repo: Optional GitHub repo URL

        Returns:
            Service ID

        Raises:
            RailwayDeploymentError: If service creation fails
        """
        query = """
        mutation ServiceCreate($input: ServiceCreateInput!) {
            serviceCreate(input: $input) {
                id
                name
            }
        }
        """

        variables = {
            "input": {
                "projectId": project_id,
                "name": service_name
            }
        }

        if github_repo:
            variables["input"]["source"] = {
                "repo": github_repo
            }

        try:
            data = self._execute_graphql(query, variables)
            service = data.get("serviceCreate")

            if not service:
                raise RailwayDeploymentError("Failed to create service")

            service_id = service["id"]
            logger.info(f"Created Railway service: {service_name} ({service_id})")
            return service_id

        except Exception as e:
            logger.error(f"Failed to create Railway service: {e}")
            raise RailwayDeploymentError(f"Service creation failed: {str(e)}")

    def set_environment_variables(
        self,
        environment_id: str,
        service_id: str,
        variables: Dict[str, str]
    ) -> bool:
        """
        Set environment variables for a service.

        Args:
            environment_id: Environment ID
            service_id: Service ID
            variables: Dictionary of environment variables

        Returns:
            True if successful

        Raises:
            RailwayDeploymentError: If setting variables fails
        """
        query = """
        mutation VariableCollectionUpsert($input: VariableCollectionUpsertInput!) {
            variableCollectionUpsert(input: $input)
        }
        """

        variables_input = {
            "environmentId": environment_id,
            "serviceId": service_id,
            "variables": variables
        }

        try:
            self._execute_graphql(query, {"input": variables_input})
            logger.info(f"Set {len(variables)} environment variables")
            return True

        except Exception as e:
            logger.error(f"Failed to set environment variables: {e}")
            raise RailwayDeploymentError(f"Failed to set environment variables: {str(e)}")

    def get_service_domain(self, environment_id: str, service_id: str) -> Optional[str]:
        """
        Get the public domain for a service.

        Args:
            environment_id: Environment ID
            service_id: Service ID

        Returns:
            Service domain URL or None if not available
        """
        query = """
        query ServiceDomain($environmentId: String!, $serviceId: String!) {
            serviceDomains(environmentId: $environmentId, serviceId: $serviceId) {
                customDomains {
                    domain
                }
                serviceDomains {
                    domain
                }
            }
        }
        """

        try:
            data = self._execute_graphql(query, {
                "environmentId": environment_id,
                "serviceId": service_id
            })

            domains = data.get("serviceDomains", {})

            # Try custom domains first
            custom_domains = domains.get("customDomains", [])
            if custom_domains:
                return f"https://{custom_domains[0]['domain']}"

            # Fall back to Railway subdomain
            service_domains = domains.get("serviceDomains", [])
            if service_domains:
                return f"https://{service_domains[0]['domain']}"

            return None

        except Exception as e:
            logger.warning(f"Failed to get service domain: {e}")
            return None

    def wait_for_deployment(
        self,
        service_id: str,
        timeout: int = 600
    ) -> Tuple[bool, Optional[str]]:
        """
        Wait for deployment to complete.

        Args:
            service_id: Service ID
            timeout: Maximum wait time in seconds

        Returns:
            Tuple of (success, deployment_url)
        """
        query = """
        query Deployments($serviceId: String!) {
            deployments(serviceId: $serviceId, first: 1) {
                edges {
                    node {
                        id
                        status
                        url
                    }
                }
            }
        }
        """

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data = self._execute_graphql(query, {"serviceId": service_id})
                deployments = data.get("deployments", {}).get("edges", [])

                if deployments:
                    deployment = deployments[0]["node"]
                    status = deployment.get("status")
                    url = deployment.get("url")

                    logger.info(f"Deployment status: {status}")

                    if status == "SUCCESS":
                        return True, url
                    elif status in ["FAILED", "CRASHED"]:
                        return False, None

                time.sleep(10)  # Poll every 10 seconds

            except Exception as e:
                logger.warning(f"Error checking deployment status: {e}")
                time.sleep(10)

        logger.error("Deployment timeout reached")
        return False, None

    def deploy_backend(
        self,
        app_name: str,
        backend_files: Dict[str, str],
        deployment_files: Dict[str, str],
        environment_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Deploy backend application to Railway.

        Args:
            app_name: Application name
            backend_files: Backend code files
            deployment_files: Deployment configuration files
            environment_vars: Environment variables to set

        Returns:
            Dict with deployment information including URL and status

        Raises:
            RailwayDeploymentError: If deployment fails
        """
        try:
            # Create project
            project_id, environment_id = self.create_project(f"{app_name}-backend")

            # Create service
            service_id = self.create_service(
                project_id=project_id,
                environment_id=environment_id,
                service_name="backend"
            )

            # Set environment variables
            self.set_environment_variables(
                environment_id=environment_id,
                service_id=service_id,
                variables=environment_vars
            )

            # Note: Railway API v2 doesn't support direct file upload via GraphQL
            # Users need to connect a GitHub repository or use Railway CLI
            # For now, we'll return instructions for manual deployment

            logger.info("Railway project created successfully")
            logger.warning("Note: File upload requires GitHub integration or Railway CLI")

            return {
                "success": True,
                "project_id": project_id,
                "service_id": service_id,
                "environment_id": environment_id,
                "status": "project_created",
                "message": "Railway project created. Connect GitHub repo or use Railway CLI to deploy files.",
                "next_steps": [
                    "Push your code to GitHub",
                    f"Connect the GitHub repository to Railway project {project_id}",
                    "Railway will automatically deploy your application"
                ]
            }

        except Exception as e:
            logger.error(f"Backend deployment failed: {e}")
            raise RailwayDeploymentError(f"Backend deployment failed: {str(e)}")

    def get_deployment_status(
        self,
        project_id: str,
        service_id: str
    ) -> Dict[str, Any]:
        """
        Get current deployment status.

        Args:
            project_id: Project ID
            service_id: Service ID

        Returns:
            Deployment status information
        """
        query = """
        query Service($serviceId: String!) {
            service(id: $serviceId) {
                id
                name
                latestDeployment {
                    id
                    status
                    createdAt
                }
            }
        }
        """

        try:
            data = self._execute_graphql(query, {"serviceId": service_id})
            service = data.get("service", {})
            deployment = service.get("latestDeployment", {})

            return {
                "service_name": service.get("name"),
                "deployment_status": deployment.get("status", "unknown"),
                "created_at": deployment.get("createdAt")
            }

        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {"error": str(e)}
