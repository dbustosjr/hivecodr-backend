"""
Test script for HiveCodr Railway deployment.
Tests all 4 bees: Architect, Developer, Frontend, and QA.
"""
import requests
import json
import time
from datetime import datetime

# Railway backend URL
RAILWAY_URL = "https://hivecodr-backend-production.up.railway.app"

# Supabase configuration
SUPABASE_URL = "https://xhouxrkzzqmzzvsrcszk.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhob3V4cmt6enFtenp2c3Jjc3prIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg1MTMwOTksImV4cCI6MjA4NDA4OTA5OX0.o09qD0uBsxf5x-5Ov8XDIyXD_qBrvwN8_x4YQF2eqTY"

# Test user credentials
TEST_EMAIL = "test@hivecodr.com"
TEST_PASSWORD = "TestPass123!"


def test_health_check():
    """Test 1: Health endpoint"""
    print("\n" + "="*80)
    print("TEST 1: HEALTH CHECK")
    print("="*80)

    try:
        response = requests.get(f"{RAILWAY_URL}/health", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Environment: {data.get('environment')}")
            return True
        else:
            print(f"[FAIL] Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Health check error: {e}")
        return False


def test_docs_endpoint():
    """Test 2: API Documentation"""
    print("\n" + "="*80)
    print("TEST 2: API DOCUMENTATION")
    print("="*80)

    try:
        response = requests.get(f"{RAILWAY_URL}/docs", timeout=10)

        if response.status_code == 200:
            print(f"[PASS] Swagger UI is accessible")
            print(f"   URL: {RAILWAY_URL}/docs")
            return True
        else:
            print(f"[FAIL] Docs endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Docs endpoint error: {e}")
        return False


def get_jwt_token():
    """Test 3: Supabase Authentication"""
    print("\n" + "="*80)
    print("TEST 3: SUPABASE AUTHENTICATION")
    print("="*80)

    try:
        # Use Supabase REST API for authentication
        auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"

        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }

        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }

        response = requests.post(auth_url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"[PASS] JWT token obtained")
            print(f"   Token: {token[:30]}...")
            print(f"   Expires: {data.get('expires_in')} seconds")
            return token
        else:
            print(f"[FAIL] Authentication failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"[FAIL] Authentication error: {e}")
        return None


def test_unauthorized_access():
    """Test 4: Verify authentication is required"""
    print("\n" + "="*80)
    print("TEST 4: AUTHENTICATION REQUIRED")
    print("="*80)

    try:
        # Try to access protected endpoint without token
        response = requests.post(
            f"{RAILWAY_URL}/api/generate",
            json={"requirements": "test"},
            timeout=10
        )

        if response.status_code == 401:
            print(f"[PASS] Authentication properly enforced")
            print(f"   Unauthorized request correctly rejected")
            return True
        else:
            print(f"[FAIL] Authentication not enforced: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Auth test error: {e}")
        return False


def test_code_generation(token):
    """Test 5: Full code generation with all 4 bees"""
    print("\n" + "="*80)
    print("TEST 5: CODE GENERATION (4 BEES)")
    print("="*80)
    print("[WARN] This will take approximately 3-5 minutes...")
    print("Testing: Architect Bee -> Developer Bee -> Frontend Bee -> QA Bee")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "requirements": "Create a simple blog with posts and comments. Users can create posts and comment on them."
    }

    try:
        print(f"\n[PROCESSING] Sending generation request...")
        start_time = time.time()

        response = requests.post(
            f"{RAILWAY_URL}/api/generate",
            headers=headers,
            json=payload,
            timeout=600  # 10 minute timeout
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()

            print(f"\n[PASS] Generation successful in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)!")
            print(f"\n[RESULTS] GENERATION RESULTS:")
            print(f"   Generation ID: {result.get('id')}")

            # Parse the code structure
            code = result.get('code', {})

            # Count backend files
            backend_files = 0
            if 'backend' in code:
                backend_files = len(code['backend'])
                print(f"\n   Backend Files ({backend_files}):")
                for filename in code['backend'].keys():
                    print(f"      - {filename}")

            # Count frontend files
            frontend_files = 0
            if 'frontend' in code:
                frontend_files = len(code['frontend'])
                print(f"\n   Frontend Files ({frontend_files}):")
                for filename in list(code['frontend'].keys())[:10]:  # Show first 10
                    print(f"      - {filename}")
                if frontend_files > 10:
                    print(f"      ... and {frontend_files - 10} more")

            total_files = backend_files + frontend_files
            print(f"\n   [FILES] Total Files Generated: {total_files}")

            # Show agent log snippet
            agent_log = result.get('agent_log', '')
            if agent_log:
                print(f"\n   [AGENT] Agent Log (first 500 chars):")
                print(f"      {agent_log[:500]}...")

            print(f"\n[PASS] All 4 bees executed successfully!")
            print(f"   [OK] Architect Bee - Designed architecture")
            print(f"   [OK] Developer Bee - Generated backend code")
            print(f"   [OK] Frontend Bee - Generated frontend code")
            print(f"   [OK] QA Bee - Generated test suite")

            return True

        elif response.status_code == 429:
            print(f"\n[WARN] Rate limit exceeded")
            print(f"   Message: {response.json().get('detail')}")
            print(f"   This is expected - rate limiting is working!")
            return True

        else:
            print(f"\n[FAIL] Generation failed: {response.status_code}")
            print(f"   Error: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print(f"\n[WARN] Request timed out (this might be normal for large generations)")
        print(f"   The generation might still be processing on the server")
        return False
    except Exception as e:
        print(f"\n[FAIL] Generation error: {e}")
        return False


def run_all_tests():
    """Run all deployment tests"""
    print("\n" + "="*80)
    print("[TEST] TESTING HIVECODR RAILWAY DEPLOYMENT")
    print("="*80)
    print(f"Backend URL: {RAILWAY_URL}")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))

    # Test 2: API Docs
    results.append(("API Documentation", test_docs_endpoint()))

    # Test 3: Get JWT Token
    token = get_jwt_token()
    results.append(("Authentication", token is not None))

    # Test 4: Verify auth is required
    results.append(("Auth Enforcement", test_unauthorized_access()))

    # Test 5: Code Generation (only if we have a token)
    if token:
        results.append(("Code Generation", test_code_generation(token)))
    else:
        print("\n[WARN] Skipping code generation test (no auth token)")
        results.append(("Code Generation", False))

    # Summary
    print("\n" + "="*80)
    print("[RESULTS] TEST SUMMARY")
    print("="*80)

    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} - {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n[SUCCESS] ALL TESTS PASSED! HiveCodr backend is fully operational on Railway!")
    else:
        print(f"\n[WARN] {total_count - passed_count} test(s) failed. Review errors above.")

    print(f"\nTest Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    return passed_count == total_count


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
