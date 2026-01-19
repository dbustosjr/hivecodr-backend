"""Vercel deployment service for automated frontend deployments."""

import requests
import time
import os
import json
import tarfile
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import logging
import hashlib

logger = logging.getLogger(__name__)


class VercelDeploymentError(Exception):
    """Exception raised when Vercel deployment fails."""
    pass


class VercelDeployService:
    """
    Service for deploying applications to Vercel using the API.

    Uses Vercel REST API for deployment.
    https://vercel.com/docs/rest-api
    """

    def __init__(self, api_token: Optional[str] = None, team_id: Optional[str] = None):
        """
        Initialize Vercel deployment service.

        Args:
            api_token: Vercel API token (if None, reads from environment)
            team_id: Optional Vercel team ID
        """
        self.api_token = api_token or os.getenv("VERCEL_API_TOKEN")
        if not self.api_token:
            raise ValueError("VERCEL_API_TOKEN not provided and not found in environment")

        self.team_id = team_id
        self.api_url = "https://api.vercel.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to Vercel API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request payload
            params: Query parameters

        Returns:
            Response data

        Raises:
            VercelDeploymentError: If the request fails
        """
        url = f"{self.api_url}{endpoint}"

        # Add team_id to params if provided
        if self.team_id:
            params = params or {}
            params["teamId"] = self.team_id

        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            error_msg = f"Vercel API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
            except:
                pass

            logger.error(error_msg)
            raise VercelDeploymentError(error_msg)

        except requests.RequestException as e:
            logger.error(f"Vercel API request failed: {e}")
            raise VercelDeploymentError(f"Failed to communicate with Vercel API: {str(e)}")

    def create_project(self, project_name: str, framework: str = "nextjs") -> Dict[str, Any]:
        """
        Create a new Vercel project.

        Args:
            project_name: Name for the project
            framework: Framework type (nextjs, react, vue, etc.)

        Returns:
            Project information

        Raises:
            VercelDeploymentError: If project creation fails
        """
        endpoint = "/v9/projects"
        data = {
            "name": project_name,
            "framework": framework
        }

        try:
            result = self._make_request("POST", endpoint, data=data)
            logger.info(f"Created Vercel project: {project_name}")
            return result

        except Exception as e:
            logger.error(f"Failed to create Vercel project: {e}")
            raise VercelDeploymentError(f"Project creation failed: {str(e)}")

    def upload_files(
        self,
        files: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Upload files to Vercel for deployment.

        Args:
            files: Dictionary of file paths to content

        Returns:
            Dictionary mapping file paths to SHA hashes

        Raises:
            VercelDeploymentError: If file upload fails
        """
        endpoint = "/v2/now/files"
        file_hashes = {}

        for file_path, content in files.items():
            try:
                # Calculate SHA-256 hash
                content_bytes = content.encode('utf-8')
                sha = hashlib.sha256(content_bytes).hexdigest()

                # Upload file
                headers = self.headers.copy()
                headers["Content-Type"] = "application/octet-stream"
                headers["x-now-digest"] = sha

                response = requests.post(
                    f"{self.api_url}{endpoint}",
                    data=content_bytes,
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()

                file_hashes[file_path] = sha
                logger.debug(f"Uploaded file: {file_path}")

            except Exception as e:
                logger.error(f"Failed to upload file {file_path}: {e}")
                raise VercelDeploymentError(f"File upload failed for {file_path}: {str(e)}")

        logger.info(f"Uploaded {len(file_hashes)} files to Vercel")
        return file_hashes

    def create_deployment(
        self,
        project_name: str,
        files: Dict[str, str],
        environment_vars: Optional[Dict[str, str]] = None,
        build_env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new deployment on Vercel.

        Args:
            project_name: Project name
            files: Dictionary of file paths to SHA hashes
            environment_vars: Runtime environment variables
            build_env_vars: Build-time environment variables

        Returns:
            Deployment information

        Raises:
            VercelDeploymentError: If deployment creation fails
        """
        endpoint = "/v13/deployments"

        # Prepare file structure for deployment
        deployment_files = []
        for file_path, sha in files.items():
            deployment_files.append({
                "file": file_path,
                "sha": sha,
                "size": len(file_path)  # Approximate
            })

        data = {
            "name": project_name,
            "files": deployment_files,
            "projectSettings": {
                "framework": "nextjs"
            }
        }

        # Add environment variables
        if environment_vars:
            env_list = [
                {"key": key, "value": value, "type": "plain"}
                for key, value in environment_vars.items()
            ]
            data["env"] = env_list

        if build_env_vars:
            build_env_list = [
                {"key": key, "value": value, "type": "plain"}
                for key, value in build_env_vars.items()
            ]
            data["buildEnv"] = build_env_list

        try:
            result = self._make_request("POST", endpoint, data=data)
            logger.info(f"Created Vercel deployment: {result.get('id')}")
            return result

        except Exception as e:
            logger.error(f"Failed to create Vercel deployment: {e}")
            raise VercelDeploymentError(f"Deployment creation failed: {str(e)}")

    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get deployment status.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment status information
        """
        endpoint = f"/v13/deployments/{deployment_id}"

        try:
            result = self._make_request("GET", endpoint)
            return result

        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {"error": str(e)}

    def wait_for_deployment(
        self,
        deployment_id: str,
        timeout: int = 600
    ) -> Tuple[bool, Optional[str]]:
        """
        Wait for deployment to complete.

        Args:
            deployment_id: Deployment ID
            timeout: Maximum wait time in seconds

        Returns:
            Tuple of (success, deployment_url)
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                status_data = self.get_deployment_status(deployment_id)

                if "error" in status_data:
                    return False, None

                ready_state = status_data.get("readyState")
                url = status_data.get("url")

                logger.info(f"Deployment state: {ready_state}")

                if ready_state == "READY":
                    return True, f"https://{url}"
                elif ready_state == "ERROR":
                    return False, None

                time.sleep(10)  # Poll every 10 seconds

            except Exception as e:
                logger.warning(f"Error checking deployment status: {e}")
                time.sleep(10)

        logger.error("Deployment timeout reached")
        return False, None

    def set_environment_variables(
        self,
        project_id: str,
        variables: Dict[str, str],
        target: List[str] = None
    ) -> bool:
        """
        Set environment variables for a project.

        Args:
            project_id: Project ID
            variables: Dictionary of environment variables
            target: Target environments (production, preview, development)

        Returns:
            True if successful

        Raises:
            VercelDeploymentError: If setting variables fails
        """
        if target is None:
            target = ["production", "preview", "development"]

        endpoint = f"/v9/projects/{project_id}/env"

        try:
            for key, value in variables.items():
                data = {
                    "key": key,
                    "value": value,
                    "type": "plain",
                    "target": target
                }

                self._make_request("POST", endpoint, data=data)
                logger.debug(f"Set environment variable: {key}")

            logger.info(f"Set {len(variables)} environment variables for project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to set environment variables: {e}")
            raise VercelDeploymentError(f"Failed to set environment variables: {str(e)}")

    def deploy_frontend(
        self,
        app_name: str,
        frontend_files: Dict[str, str],
        deployment_files: Dict[str, str],
        environment_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Deploy frontend application to Vercel.

        Args:
            app_name: Application name
            frontend_files: Frontend code files
            deployment_files: Deployment configuration files
            environment_vars: Environment variables to set

        Returns:
            Dict with deployment information including URL and status

        Raises:
            VercelDeploymentError: If deployment fails
        """
        try:
            # Create project
            project = self.create_project(f"{app_name}-frontend", framework="nextjs")
            project_id = project.get("id")

            # Combine frontend files with deployment files
            all_files = {**frontend_files, **deployment_files}

            # Upload files
            file_hashes = self.upload_files(all_files)

            # Create deployment
            deployment = self.create_deployment(
                project_name=f"{app_name}-frontend",
                files=file_hashes,
                environment_vars=environment_vars
            )

            deployment_id = deployment.get("id")
            deployment_url = deployment.get("url")

            # Wait for deployment
            success, final_url = self.wait_for_deployment(deployment_id)

            if success:
                logger.info(f"Frontend deployed successfully to {final_url}")
                return {
                    "success": True,
                    "project_id": project_id,
                    "deployment_id": deployment_id,
                    "url": final_url,
                    "status": "ready"
                }
            else:
                logger.error("Frontend deployment failed or timed out")
                return {
                    "success": False,
                    "project_id": project_id,
                    "deployment_id": deployment_id,
                    "status": "failed",
                    "message": "Deployment failed or timed out"
                }

        except Exception as e:
            logger.error(f"Frontend deployment failed: {e}")
            raise VercelDeploymentError(f"Frontend deployment failed: {str(e)}")

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a Vercel project.

        Args:
            project_id: Project ID to delete

        Returns:
            True if successful
        """
        endpoint = f"/v9/projects/{project_id}"

        try:
            self._make_request("DELETE", endpoint)
            logger.info(f"Deleted Vercel project: {project_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            return False
