"""
Simple example showing how to send code to the debug endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Example 1: Simple code
print("Example 1: Simple Code")
print("-" * 50)

code1 = """
x = 10
y = 20
result = x + y
print(f"The sum is: {result}")
"""

response = requests.post(
    f"{BASE_URL}/api/debug-code",
    json={
        "code": code1,
        "language": "python",
        "session_id": ""
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Exit Code: {data['exit_code']}")
    print(f"✓ Output: {data['execution_output']}")
    print(f"✓ Runtime: {data['runtime_duration']}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.text)

print("\n" + "="*50 + "\n")

# Example 2: Code with error
print("Example 2: Code with Error")
print("-" * 50)

code2 = """
numbers = [1, 2, 3]
print(numbers[0])  # This works
print(numbers[10]) # This will cause an error
"""

response = requests.post(
    f"{BASE_URL}/api/debug-code",
    json={
        "code": code2,
        "language": "python",
        "session_id": ""
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Exit Code: {data['exit_code']}")
    print(f"✓ Output: {data['execution_output']}")
    if data['error_type']:
        print(f"✗ Error Type: {data['error_type']}")
        print(f"✗ Error Message: {data['error_logs']}")
else:
    print(f"✗ Error: {response.status_code}")

print("\n" + "="*50 + "\n")

# Example 3: Complex code
print("Example 3: Complex Code")
print("-" * 50)

code3 = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print("Fibonacci sequence:")
for i in range(8):
    print(f"F({i}) = {fibonacci(i)}")
"""

response = requests.post(
    f"{BASE_URL}/api/debug-code",
    json={
        "code": code3,
        "language": "python",
        "session_id": ""
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"✓ Exit Code: {data['exit_code']}")
    print(f"✓ Runtime: {data['runtime_duration']}")
    print(f"✓ Memory: {data['memory_usage']}")
    print(f"\nOutput:\n{data['execution_output']}")
else:
    print(f"✗ Error: {response.status_code}")

print("\n✅ All examples completed!")
