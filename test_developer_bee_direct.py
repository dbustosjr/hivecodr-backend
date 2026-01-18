"""Direct test of Developer Bee to debug backend generation issue"""
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.agents.developer_bee import developer_bee

# Load the architecture spec from the failed generation
arch_spec_path = "C:/Users/David Jr/generated_apps/create-a-fitness-tracking-20260117-140211/architecture_spec.json"
with open(arch_spec_path, 'r') as f:
    architecture_spec = json.load(f)

requirements = """
Create a fitness tracking app with workouts, exercises, and progress tracking.

Features needed:
- Users can create and manage workout routines
- Each workout contains multiple exercises
- Track sets, reps, and weight for each exercise
- Record workout sessions with date and duration
- View progress over time with charts
- Set fitness goals and track achievements
"""

# Create a test output directory
output_dir = "C:/Users/David Jr/generated_apps/test-developer-bee-direct"
Path(output_dir).mkdir(parents=True, exist_ok=True)

print("="*80)
print("DIRECT TEST: Developer Bee Backend Generation")
print("="*80)
print(f"Architecture spec tables: {len(architecture_spec.get('database_schema', {}).get('tables', []))}")
print(f"Output directory: {output_dir}")
print("\nStarting generation...")
print("="*80)

try:
    result = developer_bee.generate_crud_code(
        requirements=requirements,
        architecture_spec=architecture_spec,
        output_dir=output_dir
    )

    print("\n" + "="*80)
    print("GENERATION RESULT")
    print("="*80)
    print(f"Files written: {result.get('files_written', 0)}")
    print(f"File paths: {list(result.get('file_paths', {}).keys())}")
    print(f"\nFile stats:")
    for filename, stats in result.get('file_stats', {}).items():
        print(f"  {filename}.py: {stats['lines']} lines, {stats['chars']} characters")

    # Check if files actually exist
    backend_dir = Path(output_dir) / "backend"
    if backend_dir.exists():
        files = list(backend_dir.glob("*.py"))
        print(f"\nActual files on disk: {len(files)}")
        for file in files:
            size = file.stat().st_size
            print(f"  {file.name}: {size} bytes")
    else:
        print(f"\nBackend directory doesn't exist!")

except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
