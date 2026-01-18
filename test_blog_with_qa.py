"""Test blog app generation with QA Bee (Phase 5)"""

import requests
import json
from datetime import datetime

# Load JWT token
with open("jwt_token.txt", "r") as f:
    token = f.read().strip()

# API endpoint
url = "http://localhost:8000/api/generate"

# Simple blog requirements
requirements = "Create a simple blog with posts and comments"

print("="*80)
print("Testing Blog App Generation with QA Bee (Phase 5)")
print("="*80)
print(f"\nEndpoint: {url}")
print(f"\nRequirements:\n{requirements}\n")
print("Sending request...")
print("This will generate backend, frontend, AND test files!\n")

start_time = datetime.now()
print(f"Starting at: {start_time.strftime('%H:%M:%S')}\n")

# Make the request
response = requests.post(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={"requirements": requirements},
    timeout=300  # 5 minute timeout
)

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print(f"Completed at: {end_time.strftime('%H:%M:%S')}")
print(f"Status Code: {response.status_code}")
print("="*80 + "\n")

if response.status_code == 200:
    print("SUCCESS!\n")
    data = response.json()

    print(f"Generation ID: {data['id']}")
    print(f"Created At: {data['created_at']}\n")

    # Parse the code response
    code_data = data.get('code', {})
    output_dir = code_data.get('output_directory', 'N/A')

    print("="*80)
    print("OUTPUT DIRECTORY:")
    print("="*80)
    print(f"All generated files written to: {output_dir}\n")

    # Backend files
    backend_data = code_data.get('backend', {})
    print("="*80)
    print("BACKEND FILES:")
    print("="*80)
    if backend_data:
        for filename, stats in backend_data.items():
            if isinstance(stats, dict) and 'lines' in stats:
                print(f"  {filename}:")
                print(f"    - Path: {stats.get('path', 'N/A')}")
                print(f"    - Lines: {stats.get('lines', 0)}")
                print(f"    - Characters: {stats.get('chars', 0)}\n")
    else:
        print("  No backend files information available\n")

    # Frontend files
    frontend_data = code_data.get('frontend', {})
    print("="*80)
    print("FRONTEND FILES:")
    print("="*80)
    if frontend_data:
        total_files = len(frontend_data)
        print(f"  Total files: {total_files}\n")

        # Group by type
        config_files = []
        app_files = []
        component_files = []

        for filename, stats in frontend_data.items():
            if isinstance(stats, dict) and 'lines' in stats:
                if any(x in filename for x in ['package.json', 'tsconfig', 'tailwind', 'next.config']):
                    config_files.append((filename, stats))
                elif 'app/' in filename:
                    app_files.append((filename, stats))
                else:
                    component_files.append((filename, stats))

        if config_files:
            print(f"  Configuration files ({len(config_files)}):")
            for filename, stats in config_files:
                print(f"    - {filename}: {stats.get('lines', 0)} lines")

        if app_files:
            print(f"\n  App files ({len(app_files)}):")
            for filename, stats in app_files:
                print(f"    - {filename}: {stats.get('lines', 0)} lines")

        if component_files:
            print(f"\n  Component files ({len(component_files)}):")
            for filename, stats in component_files:
                print(f"    - {filename}: {stats.get('lines', 0)} lines")

        print()
    else:
        print("  No frontend files information available\n")

    # Test files (NEW in Phase 5!)
    tests_data = code_data.get('tests', {})
    print("="*80)
    print("TEST FILES (QA BEE):")
    print("="*80)
    if tests_data:
        for filename, stats in tests_data.items():
            if isinstance(stats, dict) and 'lines' in stats:
                print(f"  {filename}.py:")
                print(f"    - Path: {stats.get('path', 'N/A')}")
                print(f"    - Lines: {stats.get('lines', 0)}")
                print(f"    - Characters: {stats.get('chars', 0)}\n")
    else:
        print("  No test files information available\n")

    # Summary
    backend_count = len([k for k, v in backend_data.items() if isinstance(v, dict) and 'lines' in v]) if backend_data else 0
    frontend_count = len([k for k, v in frontend_data.items() if isinstance(v, dict) and 'lines' in v]) if frontend_data else 0
    test_count = len([k for k, v in tests_data.items() if isinstance(v, dict) and 'lines' in v]) if tests_data else 0

    print("="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"- Output directory: {output_dir}")
    print(f"- Backend files: {backend_count}")
    print(f"- Frontend files: {frontend_count}")
    print(f"- Test files: {test_count}")
    print(f"- Total files: {backend_count + frontend_count + test_count}")
    print(f"- Duration: {duration:.1f} seconds\n")

    print("All files have been written to disk!")
    print("You can now navigate to the output directory to see the generated code.\n")

else:
    print("ERROR!\n")
    print(f"Response: {response.text}\n")
