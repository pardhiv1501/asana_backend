#!/usr/bin/env python
"""
API Validation Script for Asana Backend Replica

This script tests various API endpoints and validates that responses
match expected formats based on the Asana OpenAPI specification.
"""

import requests
import json
import sys
from typing import Dict, Any, List


class APIValidator:
    def __init__(self, base_url: str = "http://localhost:8000/api/1.0"):
        self.base_url = base_url
        self.session = requests.Session()
        self.passed_tests = 0
        self.failed_tests = 0

    def test_endpoint(self, endpoint: str, method: str = 'GET', expected_status: int = 200,
                     data: Dict[str, Any] = None, description: str = "") -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        print(f"\nTesting: {description or endpoint}")
        print(f"Method: {method}, URL: {url}")

        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            print(f"Status Code: {response.status_code} (Expected: {expected_status})")

            if response.status_code == expected_status:
                print("[PASS] Status code matches expected")
                self.passed_tests += 1

                # Try to parse JSON response
                try:
                    json_data = response.json()
                    print("[PASS] Response is valid JSON")

                    # Basic structure validation
                    if self.validate_response_structure(endpoint, json_data):
                        print("[PASS] Response structure is valid")
                    else:
                        print("[FAIL] Response structure validation failed")
                        self.failed_tests += 1
                        return False

                except json.JSONDecodeError:
                    # Allow HTML responses for documentation endpoints
                    if 'swagger' in endpoint.lower() or 'redoc' in endpoint.lower():
                        print("[PASS] HTML response (expected for documentation)")
                    elif response.status_code == 200:
                        print("[FAIL] Expected JSON response but got non-JSON")
                        self.failed_tests += 1
                        return False
                    else:
                        print("[PASS] Non-JSON response (expected for error status)")

                return True
            else:
                print(f"[FAIL] Status code mismatch: got {response.status_code}, expected {expected_status}")
                self.failed_tests += 1
                return False

        except requests.exceptions.RequestException as e:
            print(f"[FAIL] Request failed: {e}")
            self.failed_tests += 1
            return False

    def validate_response_structure(self, endpoint: str, data: Dict[str, Any]) -> bool:
        """Validate basic response structure"""
        # Check for common Asana API response patterns
        if endpoint.startswith('users') or endpoint.startswith('workspaces') or endpoint.startswith('projects') or endpoint.startswith('tasks') or endpoint.startswith('teams') or endpoint.startswith('tags'):
            # All endpoints should have data field
            if 'data' not in data:
                print("  - Missing data field in response")
                return False

            # List endpoints will have pagination info if paginated, single objects won't
            if isinstance(data['data'], list):
                # This is a list endpoint - pagination fields are optional for small lists
                # Check that data contains objects with required fields
                if data['data'] and len(data['data']) > 0:
                    sample_obj = data['data'][0]
                    if 'gid' not in sample_obj or 'resource_type' not in sample_obj:
                        print("  - Missing required gid/resource_type fields in list items")
                        return False
            else:
                # This is a single object endpoint
                if 'gid' not in data['data'] or 'resource_type' not in data['data']:
                    print("  - Missing required gid/resource_type fields in single object")
                    return False

        return True

    def run_tests(self) -> bool:
        """Run all API validation tests"""
        print("=" * 60)
        print("ASANA API VALIDATION TESTS")
        print("=" * 60)

        # Test basic endpoints
        tests = [
            # Users endpoints
            ("users/", "GET", 200, None, "List all users"),
            ("users/me", "GET", 200, None, "Get current user"),

            # Workspaces endpoints
            ("workspaces/", "GET", 200, None, "List all workspaces"),
            ("workspaces/ddaa32b802ad49e0", "GET", 200, None, "Get specific workspace"),
            ("workspaces/ddaa32b802ad49e0/projects", "GET", 200, None, "Get workspace projects"),
            ("workspaces/ddaa32b802ad49e0/tasks", "GET", 200, None, "Get workspace tasks"),
            ("workspaces/ddaa32b802ad49e0/teams", "GET", 200, None, "Get workspace teams"),

            # Projects endpoints
            ("projects/", "GET", 200, None, "List all projects"),
            ("projects/230e06d205f04b50", "GET", 200, None, "Get specific project"),
            ("projects/230e06d205f04b50/tasks", "GET", 200, None, "Get project tasks"),

            # Tasks endpoints
            ("tasks/", "GET", 200, None, "List all tasks"),
            ("tasks/d6b34d55f336489b", "GET", 200, None, "Get specific task"),

            # Teams endpoints
            ("teams/", "GET", 200, None, "List all teams"),

            # Tags endpoints
            ("tags/", "GET", 200, None, "List all tags"),

            # Swagger documentation (returns HTML, not JSON)
            ("../../swagger/", "GET", 200, None, "Swagger documentation"),
        ]

        for endpoint, method, expected_status, data, description in tests:
            self.test_endpoint(endpoint, method, expected_status, data, description)

        # Test creating a new user
        import time
        new_user_data = {
            "name": "Test User",
            "email": f"test.user.{int(time.time())}@example.com"
        }
        self.test_endpoint("users/", "POST", 201, new_user_data, "Create new user")

        # Test creating a new workspace
        new_workspace_data = {
            "name": "Test Workspace",
            "is_organization": False
        }
        self.test_endpoint("workspaces/", "POST", 201, new_workspace_data, "Create new workspace")

        # Print results
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Total: {self.passed_tests + self.failed_tests}")

        if self.failed_tests == 0:
            print("SUCCESS: All tests passed!")
            return True
        else:
            print(f"FAILED: {self.failed_tests} test(s) failed")
            return False


def main():
    """Main function"""
    validator = APIValidator()

    try:
        success = validator.run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()