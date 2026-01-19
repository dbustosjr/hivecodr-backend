"""API endpoint for code generation."""

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from datetime import datetime
from pathlib import Path
import os
import re
from app.models.schemas import GenerateRequest, GenerateResponse
from app.core.auth import get_current_user, get_supabase_client, CurrentUser
from app.core.rate_limiter import check_rate_limit, increment_usage
from app.core.complexity_analyzer import complexity_analyzer
from app.agents.architect_bee import architect_bee
from app.agents.developer_bee import developer_bee
from app.agents.frontend_bee import frontend_bee
from app.agents.qa_bee import qa_bee
from app.agents.devops_bee import DevOpsBeeAgent
from app.services.railway_deploy import RailwayDeployService, RailwayDeploymentError
from app.services.vercel_deploy import VercelDeployService, VercelDeploymentError
from app.core.config import settings
import time


router = APIRouter()


def create_output_directory(requirements: str) -> str:
    """
    Create a timestamped output directory for generated code.

    Args:
        requirements: User requirements (used to create a meaningful folder name)

    Returns:
        Path to the created output directory
    """
    # Create a safe folder name from requirements
    # Extract first few words and make filesystem-safe
    folder_name = re.sub(r'[^a-zA-Z0-9\s-]', '', requirements)
    folder_name = '-'.join(folder_name.split()[:4]).lower()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder_name = f"{folder_name}-{timestamp}"

    # Create base generated_apps directory
    base_dir = Path("C:/Users/David Jr/generated_apps")
    base_dir.mkdir(parents=True, exist_ok=True)

    # Create specific app directory
    output_dir = base_dir / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    return str(output_dir)


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate full-stack application from requirements",
    description="Generates complete FastAPI backend + Next.js 14 frontend based on plain English requirements using a five-agent workflow (Architect, Developer, Frontend, QA, and DevOps Bees). Optionally deploys to Railway (backend) and Vercel (frontend)."
)
async def generate_code(
    request: GenerateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Generate full-stack application from plain English requirements.

    Uses a five-agent sequential workflow:
    Phase 0: Complexity Analysis
    Phase 1: Architect Bee - Analyzes requirements and creates technical specification
    Phase 2: Developer Bee - Generates FastAPI backend code based on the architecture specification
    Phase 3: Frontend Bee - Generates Next.js 14 frontend code based on the backend
    Phase 4: QA Bee - Generates comprehensive test suite for backend and frontend
    Phase 5: DevOps Bee - Generates deployment configurations (Dockerfile, railway.json, vercel.json, etc.)
    Phase 6 (Optional): Automated deployment to Railway (backend) and Vercel (frontend) if deploy=true

    Args:
        request: Generation request with requirements, optional deploy and app_name
        current_user: Authenticated user from JWT token
        supabase: Supabase client for database operations

    Returns:
        GenerateResponse: Generated backend, frontend, tests, and deployment configs with agent logs.
                         If deploy=true, includes live URLs for deployed applications.

    Raises:
        HTTPException: If rate limit exceeded or generation fails
    """
    try:
        # Check rate limit
        await check_rate_limit(current_user, supabase)

        # PHASE 0: Analyze Complexity
        print(f"\n{'='*80}")
        print("PHASE 0: ANALYZING REQUIREMENT COMPLEXITY")
        print(f"{'='*80}\n")

        complexity_analysis = complexity_analyzer.analyze(request.requirements)

        print(f"Complexity Score: {complexity_analysis['complexity_score']}/100")
        print(f"Complexity Level: {complexity_analysis['complexity_level'].upper()}")
        print(f"Estimated Models: {complexity_analysis['model_count_estimate']}")
        print(f"Generation Strategy: {complexity_analysis['generation_strategy']}")

        if complexity_analysis['core_features']:
            print(f"Core Features: {', '.join(complexity_analysis['core_features'])}")
        if complexity_analysis['advanced_features']:
            print(f"Advanced Features: {', '.join(complexity_analysis['advanced_features'])}")

        # Create timestamped output directory for generated files
        output_dir = create_output_directory(request.requirements)
        print(f"\nCreated output directory: {output_dir}\n")

        # Save complexity analysis
        import json
        complexity_path = Path(output_dir) / "complexity_analysis.json"
        complexity_path.write_text(json.dumps(complexity_analysis, indent=2), encoding='utf-8')

        # PHASE 1: Architect Bee - Analyze requirements and create specification
        print(f"\n{'='*80}")
        print("PHASE 1: ARCHITECTURE DESIGN")
        print(f"{'='*80}\n")

        architecture_result = architect_bee.analyze_requirements(request.requirements)
        architecture_spec = architecture_result["specification"]
        architect_log = architecture_result["raw_output"]

        # Save architecture spec to output directory
        arch_spec_path = Path(output_dir) / "architecture_spec.json"
        arch_spec_path.write_text(json.dumps(architecture_spec, indent=2), encoding='utf-8')

        print(f"[OK] Architecture specification created:")
        print(f"   - Tables: {len(architecture_spec.get('database_schema', {}).get('tables', []))}")
        print(f"   - API Endpoints: {len(architecture_spec.get('api_endpoints', []))}")

        # PHASE 2: Developer Bee - Generate code with retry logic
        print(f"\n{'='*80}")
        print("PHASE 2: BACKEND CODE GENERATION")
        print(f"{'='*80}\n")

        backend_result = developer_bee.generate_crud_code_with_retry(
            requirements=request.requirements,
            architecture_spec=architecture_spec,
            output_dir=output_dir,
            max_attempts=3
        )
        developer_log = backend_result.get("agent_log", "")

        # DEBUG: Log what Developer Bee returned
        print(f"[DEBUG API] backend_result keys: {list(backend_result.keys())}")
        print(f"[DEBUG API] file_paths: {backend_result.get('file_paths', {})}")
        print(f"[DEBUG API] files_written: {backend_result.get('files_written', 0)}")
        print(f"[DEBUG API] status: {backend_result.get('status', 'success')}")

        backend_status = backend_result.get("status", "success")
        backend_files = backend_result.get("files_written", 0)

        if backend_status == "failed":
            print(f"\n[WARNING] Backend generation failed after {backend_result.get('retry_info', {}).get('attempts', 0)} attempts")
            print(f"   Continuing with frontend generation using minimal backend...")
        else:
            print(f"\n[OK] Backend code generated:")
            print(f"   - Files written: {backend_files}")
            print(f"   - Attempts: {backend_result.get('retry_info', {}).get('attempts', 1)}")
            print(f"   - Strategy: {backend_result.get('retry_info', {}).get('final_attempt_type', 'N/A')}")

        # PHASE 3: Frontend Bee - Generate Next.js frontend with retry logic
        print(f"\n{'='*80}")
        print("PHASE 3: FRONTEND CODE GENERATION")
        print(f"{'='*80}\n")

        # Prepare backend code for frontend generation
        backend_code = {}
        if 'file_paths' in backend_result and backend_result['file_paths']:
            # Read files from disk
            for filename, filepath in backend_result['file_paths'].items():
                try:
                    backend_code[filename] = Path(filepath).read_text(encoding='utf-8')
                except Exception:
                    backend_code[filename] = ""
        elif 'code' in backend_result:
            backend_code = backend_result['code']

        # Provide minimal backend if generation failed
        if not backend_code or backend_status == "failed":
            print("[WARNING] Using minimal backend code for frontend generation")
            backend_code = {
                "models": "# Backend generation incomplete - placeholder",
                "schemas": "",
                "routes": "",
                "main": ""
            }

        frontend_result = frontend_bee.generate_frontend_code_with_retry(
            backend_code=backend_code,
            requirements=request.requirements,
            architecture_spec=architecture_spec,
            output_dir=output_dir,
            max_attempts=3
        )
        frontend_log = frontend_result.get("agent_log", "")

        frontend_status = frontend_result.get("status", "success")
        frontend_files = frontend_result.get("files_written", 0)

        if frontend_status == "failed":
            print(f"\n[WARNING] Frontend generation failed after {frontend_result.get('retry_info', {}).get('attempts', 0)} attempts")
        else:
            print(f"\n[OK] Frontend code generated:")
            print(f"   - Files written: {frontend_files}")
            print(f"   - Attempts: {frontend_result.get('retry_info', {}).get('attempts', 1)}")
            print(f"   - Strategy: {frontend_result.get('retry_info', {}).get('final_attempt_type', 'N/A')}")

        # PHASE 4: QA Bee - Generate comprehensive test suite
        print(f"\n{'='*80}")
        print("PHASE 4: COMPREHENSIVE TEST SUITE GENERATION")
        print(f"{'='*80}\n")

        # Only generate tests if backend succeeded
        if backend_status == "success" and backend_files > 0:
            # Prepare frontend code for test generation
            frontend_code = {}
            if 'file_paths' in frontend_result and frontend_result['file_paths']:
                # Read frontend component files from disk
                for filename, filepath in frontend_result['file_paths'].items():
                    try:
                        # Only include component files for testing
                        if 'components/' in filename or 'pages/' in filename or 'app/' in filename:
                            frontend_code[filename] = Path(filepath).read_text(encoding='utf-8')
                    except Exception:
                        pass
            elif 'code' in frontend_result:
                frontend_code = frontend_result['code']

            test_result = qa_bee.generate_test_suite_with_retry(
                backend_code=backend_code,
                architecture_spec=architecture_spec,
                requirements=request.requirements,
                frontend_code=frontend_code if frontend_code else None,
                output_dir=output_dir,
                max_attempts=3
            )
            qa_log = test_result.get("agent_log", "")

            test_status = test_result.get("status", "success")
            test_files = test_result.get("files_written", 0)
            test_counts = test_result.get("test_counts", {})
            coverage_estimates = test_result.get("coverage_estimates", {})

            if test_status == "failed":
                print(f"\n[WARNING] Test generation failed after {test_result.get('retry_info', {}).get('attempts', 0)} attempts")
                print(f"   Backend and frontend still succeeded - tests are optional")
            else:
                print(f"\n[OK] Comprehensive test suite generated:")
                print(f"   - Backend tests: {test_counts.get('backend', 0)} files (Coverage: {coverage_estimates.get('backend', 'N/A')})")
                print(f"   - Frontend tests: {test_counts.get('frontend', 0)} files (Coverage: {coverage_estimates.get('frontend', 'N/A')})")
                print(f"   - E2E tests: {test_counts.get('e2e', 0)} files ({coverage_estimates.get('e2e', 'N/A')})")
                print(f"   - Security tests: {test_counts.get('security', 0)} files ({coverage_estimates.get('security', 'N/A')})")
                print(f"   - Contract tests: {test_counts.get('contract', 0)} files ({coverage_estimates.get('contracts', 'N/A')})")
                print(f"   - TOTAL test files: {test_files}")
                print(f"   - Attempts: {test_result.get('retry_info', {}).get('attempts', 1)}")
                print(f"   - Strategy: {test_result.get('retry_info', {}).get('final_attempt_type', 'N/A')}")
        else:
            print(f"\n[SKIP] Skipping test generation (backend generation failed or no backend files)")
            test_result = {
                "file_paths": {},
                "file_stats": {},
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
                "status": "skipped"
            }
            qa_log = "Test generation skipped - no backend code available"
            test_status = "skipped"
            test_files = 0
            test_counts = test_result["test_counts"]
            coverage_estimates = test_result["coverage_estimates"]

        # PHASE 5: DevOps Bee - Generate deployment configurations
        print(f"\n{'='*80}")
        print("PHASE 5: DEPLOYMENT CONFIGURATION GENERATION")
        print(f"{'='*80}\n")

        devops_bee = DevOpsBeeAgent()
        deployment_config = {}
        deployment_files = 0
        devops_log = ""
        deployment_status = "success"

        try:
            # Generate deployment configurations
            deployment_config = devops_bee.generate_deployment_configs(
                app_name=request.app_name or "generated-app",
                architecture=architecture_spec,
                backend_files=backend_code,
                frontend_files={}  # We'll read from disk if needed
            )

            # Write deployment files to output directory
            deployment_dir = Path(output_dir) / "deployment"
            deployment_dir.mkdir(parents=True, exist_ok=True)

            deployment_files_data = deployment_config.get("deployment_files", {})
            for filename, content in deployment_files_data.items():
                file_path = deployment_dir / filename
                file_path.write_text(content, encoding='utf-8')
                deployment_files += 1

            devops_log = f"Generated {deployment_files} deployment configuration files"

            print(f"[OK] Deployment configurations generated:")
            print(f"   - Files written: {deployment_files}")
            print(f"   - Files: {', '.join(deployment_files_data.keys())}")

        except Exception as e:
            print(f"[WARNING] Deployment config generation failed: {e}")
            deployment_status = "failed"
            devops_log = f"Deployment config generation failed: {str(e)}"

        # PHASE 6 (Optional): Deploy to Railway and Vercel
        deployed = False
        backend_url = None
        frontend_url = None
        deployment_time_str = None
        deployment_result = {}

        if request.deploy and request.app_name:
            print(f"\n{'='*80}")
            print("PHASE 6: AUTOMATED DEPLOYMENT")
            print(f"{'='*80}\n")

            deployment_start = time.time()

            # Prepare environment variables for backend
            backend_env_vars = {}
            if deployment_config.get("environment_variables", {}).get("backend"):
                for var_name, var_info in deployment_config["environment_variables"]["backend"].items():
                    if var_info.get("required"):
                        # Get from settings if available
                        if hasattr(settings, var_name):
                            backend_env_vars[var_name] = getattr(settings, var_name)

            # Deploy backend to Railway
            try:
                if settings.RAILWAY_API_TOKEN:
                    print("[DEPLOYING] Backend to Railway...")
                    railway_service = RailwayDeployService(settings.RAILWAY_API_TOKEN)

                    backend_deployment = railway_service.deploy_backend(
                        app_name=request.app_name,
                        backend_files=backend_code,
                        deployment_files=deployment_files_data,
                        environment_vars=backend_env_vars
                    )

                    if backend_deployment.get("success"):
                        # Note: Railway requires GitHub integration
                        deployment_result["backend"] = backend_deployment
                        print(f"[OK] Railway project created: {backend_deployment.get('project_id')}")
                        print(f"[INFO] Connect your GitHub repository to complete deployment")
                    else:
                        print(f"[WARNING] Backend deployment setup incomplete")

                else:
                    print("[WARNING] RAILWAY_API_TOKEN not configured - skipping backend deployment")

            except RailwayDeploymentError as e:
                print(f"[ERROR] Railway deployment failed: {e}")
                deployment_result["backend_error"] = str(e)

            # Deploy frontend to Vercel
            try:
                if settings.VERCEL_API_TOKEN:
                    print("[DEPLOYING] Frontend to Vercel...")
                    vercel_service = VercelDeployService(settings.VERCEL_API_TOKEN)

                    # Prepare frontend files
                    frontend_files_dict = {}
                    if 'file_paths' in frontend_result and frontend_result['file_paths']:
                        for filename, filepath in frontend_result['file_paths'].items():
                            try:
                                frontend_files_dict[filename] = Path(filepath).read_text(encoding='utf-8')
                            except Exception:
                                pass

                    # Prepare frontend environment variables
                    frontend_env_vars = {
                        "NEXT_PUBLIC_API_URL": backend_url or f"https://{request.app_name}.railway.app"
                    }

                    frontend_deployment = vercel_service.deploy_frontend(
                        app_name=request.app_name,
                        frontend_files=frontend_files_dict,
                        deployment_files=deployment_files_data,
                        environment_vars=frontend_env_vars
                    )

                    if frontend_deployment.get("success"):
                        frontend_url = frontend_deployment.get("url")
                        deployment_result["frontend"] = frontend_deployment
                        deployed = True
                        print(f"[OK] Frontend deployed to: {frontend_url}")
                    else:
                        print(f"[WARNING] Frontend deployment failed")

                else:
                    print("[WARNING] VERCEL_API_TOKEN not configured - skipping frontend deployment")

            except VercelDeploymentError as e:
                print(f"[ERROR] Vercel deployment failed: {e}")
                deployment_result["frontend_error"] = str(e)

            deployment_elapsed = time.time() - deployment_start
            deployment_time_str = f"{int(deployment_elapsed // 60)}m {int(deployment_elapsed % 60)}s"

            print(f"\n[OK] Deployment phase completed in {deployment_time_str}")

        # Create generation summary
        print(f"\n{'='*80}")
        print("GENERATION SUMMARY")
        print(f"{'='*80}\n")

        total_files = backend_files + frontend_files + test_files + deployment_files
        success_rate = "Complete" if backend_status == "success" and frontend_status == "success" else "Partial"

        print(f"Overall Status: {success_rate}")
        print(f"Total Files Generated: {total_files}")
        print(f"  - Backend: {backend_files} files ({backend_status})")
        print(f"  - Frontend: {frontend_files} files ({frontend_status})")
        print(f"  - Tests: {test_files} files ({test_status})")
        print(f"  - Deployment: {deployment_files} files ({deployment_status})")
        print(f"    • Backend Tests: {test_counts.get('backend', 0)} files - Coverage: {coverage_estimates.get('backend', 'N/A')}")
        print(f"    • Frontend Tests: {test_counts.get('frontend', 0)} files - Coverage: {coverage_estimates.get('frontend', 'N/A')}")
        print(f"    • E2E Tests: {test_counts.get('e2e', 0)} files - {coverage_estimates.get('e2e', 'N/A')}")
        print(f"    • Security Tests: {test_counts.get('security', 0)} files - {coverage_estimates.get('security', 'N/A')}")
        print(f"    • Contract Tests: {test_counts.get('contract', 0)} files - {coverage_estimates.get('contracts', 'N/A')}")
        print(f"Complexity Level: {complexity_analysis['complexity_level']}")
        print(f"Output Directory: {output_dir}")

        if deployed:
            print(f"\nDEPLOYMENT STATUS:")
            print(f"  - Deployed: Yes")
            if backend_url:
                print(f"  - Backend URL: {backend_url}")
            if frontend_url:
                print(f"  - Frontend URL: {frontend_url}")
            if deployment_time_str:
                print(f"  - Deployment Time: {deployment_time_str}")
        elif request.deploy:
            print(f"\nDEPLOYMENT STATUS: Attempted but incomplete (see logs above)")
        elif deployment_files > 0:
            print(f"\nDEPLOYMENT CONFIGS: Ready for manual deployment")

        # Combine logs from all phases
        combined_log = f"""
=== PHASE 0: COMPLEXITY ANALYSIS ===
Complexity Score: {complexity_analysis['complexity_score']}/100
Complexity Level: {complexity_analysis['complexity_level']}
Estimated Models: {complexity_analysis['model_count_estimate']}
Generation Strategy: {complexity_analysis['generation_strategy']}
Core Features: {', '.join(complexity_analysis.get('core_features', []))}
Advanced Features: {', '.join(complexity_analysis.get('advanced_features', []))}

=== PHASE 1: ARCHITECTURE DESIGN ===
Status: Success
Tables: {len(architecture_spec.get('database_schema', {}).get('tables', []))}
API Endpoints: {len(architecture_spec.get('api_endpoints', []))}

{architect_log[:2000]}  [Truncated for storage]

=== PHASE 2: BACKEND CODE GENERATION ===
Status: {backend_status}
Files Written: {backend_files}
Attempts: {backend_result.get('retry_info', {}).get('attempts', 1)}
Final Strategy: {backend_result.get('retry_info', {}).get('final_attempt_type', 'N/A')}

{developer_log[:2000]}  [Truncated for storage]

=== PHASE 3: FRONTEND CODE GENERATION ===
Status: {frontend_status}
Files Written: {frontend_files}
Attempts: {frontend_result.get('retry_info', {}).get('attempts', 1)}
Final Strategy: {frontend_result.get('retry_info', {}).get('final_attempt_type', 'N/A')}

{frontend_log[:2000]}  [Truncated for storage]

=== PHASE 4: TEST SUITE GENERATION ===
Status: {test_status}
Test Files Written: {test_files}
Estimated Coverage: {estimated_coverage}
Attempts: {test_result.get('retry_info', {}).get('attempts', 1) if test_status != 'skipped' else 0}
Final Strategy: {test_result.get('retry_info', {}).get('final_attempt_type', 'N/A') if test_status != 'skipped' else 'N/A'}

{qa_log[:2000]}  [Truncated for storage]

=== PHASE 5: DEPLOYMENT CONFIGURATION ===
Status: {deployment_status}
Deployment Files Written: {deployment_files}

{devops_log[:2000]}  [Truncated for storage]

=== PHASE 6: AUTOMATED DEPLOYMENT ===
Deployed: {deployed}
Backend URL: {backend_url or 'N/A'}
Frontend URL: {frontend_url or 'N/A'}
Deployment Time: {deployment_time_str or 'N/A'}

=== SUMMARY ===
Overall Status: {success_rate}
Total Files: {total_files}
  - Backend: {backend_files}
  - Frontend: {frontend_files}
  - Tests: {test_files} (Coverage: {estimated_coverage})
  - Deployment: {deployment_files}
Output Directory: {output_dir}
Deployed: {deployed}
"""

        # Store generation in database with file paths instead of full code
        generation_data = {
            "user_id": current_user.user_id,
            "requirements": request.requirements,
            "generated_code": {
                "complexity_analysis": {
                    "score": complexity_analysis['complexity_score'],
                    "level": complexity_analysis['complexity_level'],
                    "model_count": complexity_analysis['model_count_estimate'],
                    "strategy": complexity_analysis['generation_strategy']
                },
                "output_directory": output_dir,
                "backend": {
                    "file_paths": backend_result.get("file_paths", {}),
                    "file_stats": backend_result.get("file_stats", {}),
                    "files_written": backend_result.get("files_written", 0),
                    "status": backend_status,
                    "retry_info": backend_result.get("retry_info", {})
                },
                "frontend": {
                    "file_paths": frontend_result.get("file_paths", {}),
                    "file_stats": frontend_result.get("file_stats", {}),
                    "files_written": frontend_result.get("files_written", 0),
                    "status": frontend_status,
                    "retry_info": frontend_result.get("retry_info", {})
                },
                "tests": {
                    "file_paths": test_result.get("file_paths", {}),
                    "file_stats": test_result.get("file_stats", {}),
                    "files_written": test_result.get("files_written", 0),
                    "estimated_coverage": test_result.get("estimated_coverage", "0%"),
                    "status": test_status,
                    "retry_info": test_result.get("retry_info", {})
                },
                "deployment": {
                    "files_written": deployment_files,
                    "status": deployment_status,
                    "deployed": deployed,
                    "backend_url": backend_url,
                    "frontend_url": frontend_url,
                    "deployment_time": deployment_time_str,
                    "deployment_result": deployment_result
                },
                "overall_status": success_rate,
                "total_files": total_files
            },
            "agent_outputs": {
                "complexity_analysis_path": str(complexity_path),
                "architecture_spec_path": str(arch_spec_path),
                "architect_log": architect_log[:5000],  # Truncate long logs
                "developer_log": developer_log[:5000],
                "frontend_log": frontend_log[:5000],
                "qa_log": qa_log[:5000],  # QA Bee log
                "devops_log": devops_log[:5000],  # DevOps Bee log
                "combined_log": combined_log[:10000]
            },
            "created_at": datetime.utcnow().isoformat()
        }

        db_response = supabase.table("generations").insert(generation_data).execute()

        if not db_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store generation in database"
            )

        # Increment user usage
        await increment_usage(current_user, supabase)

        generation_id = db_response.data[0]["id"]

        # Return response with file paths and metadata instead of full code
        return GenerateResponse(
            id=generation_id,
            code={
                "output_directory": output_dir,
                "backend": backend_result.get("file_stats", {}),
                "frontend": frontend_result.get("file_stats", {}),
                "deployment": {"files_written": deployment_files}
            },
            agent_log=combined_log,
            created_at=datetime.fromisoformat(generation_data["created_at"]),
            deployed=deployed,
            deployment_status={
                "backend": "live" if backend_url else "pending" if request.deploy else "not_attempted",
                "frontend": "live" if frontend_url else "pending" if request.deploy else "not_attempted"
            } if request.deploy or deployed else None,
            backend_url=backend_url,
            frontend_url=frontend_url,
            deployment_time=deployment_time_str,
            deployment_configs_ready=deployment_files > 0
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {str(e)}"
        )
