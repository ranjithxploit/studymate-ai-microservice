"""
Test script to verify Markdown and Mermaid formatting in API responses
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_explanation_markdown():
    """Test that explanation endpoint returns Markdown-formatted content"""
    print("\n" + "="*60)
    print("TEST 1: Explanation with Markdown Formatting")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/explain",
        json={
            "question": "What is a list in Python?",
            "levels": "beginner",
            "session_id": ""
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Status: {response.status_code}")
        print(f"✓ Session ID: {data['session_id']}")
        
        # Check for Markdown formatting indicators
        explanation = data['explanation']
        example = data['example']
        
        print("\n--- Explanation (checking for Markdown) ---")
        print(explanation[:500] + "..." if len(explanation) > 500 else explanation)
        
        markdown_indicators = {
            "Headers": any(x in explanation for x in ['##', '###']),
            "Bold": '**' in explanation,
            "Code": '`' in explanation,
            "Lists": any(x in explanation for x in ['\n- ', '\n* ']),
        }
        
        print("\n--- Markdown Formatting Detected ---")
        for feature, present in markdown_indicators.items():
            status = "✓" if present else "✗"
            print(f"{status} {feature}: {'Yes' if present else 'No'}")
        
        print("\n--- Example (first 300 chars) ---")
        print(example[:300] + "..." if len(example) > 300 else example)
        
        return data['session_id']
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(response.text)
        return None

def test_flowchart_mermaid(session_id):
    """Test that flowchart endpoint returns proper Mermaid code"""
    print("\n" + "="*60)
    print("TEST 2: Flowchart with Mermaid Diagram")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/api/flowchart",
        json={
            "session_id": session_id,
            "concept": "how a for loop works"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Status: {response.status_code}")
        print(f"✓ Concept: {data['concept']}")
        
        # Check for required fields
        has_mermaid = 'mermaid_code' in data
        has_steps = 'steps' in data and isinstance(data['steps'], list)
        
        print(f"\n✓ Has 'mermaid_code' field: {has_mermaid}")
        print(f"✓ Has 'steps' array: {has_steps}")
        
        if has_mermaid:
            mermaid_code = data['mermaid_code']
            print("\n--- Mermaid Code ---")
            print(mermaid_code)
            
            # Check for valid Mermaid syntax
            mermaid_checks = {
                "Starts with graph": mermaid_code.strip().startswith('graph'),
                "Has nodes": '[' in mermaid_code and ']' in mermaid_code,
                "Has arrows": '-->' in mermaid_code,
            }
            
            print("\n--- Mermaid Validation ---")
            for check, result in mermaid_checks.items():
                status = "✓" if result else "✗"
                print(f"{status} {check}: {'Yes' if result else 'No'}")
        
        if has_steps:
            print(f"\n--- Steps ({len(data['steps'])} total) ---")
            for i, step in enumerate(data['steps'], 1):
                print(f"{i}. {step}")
        
        print("\n" + "="*60)
        print("✓ All tests completed successfully!")
        print("="*60)
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Testing Output Formatting Updates")
    print("Make sure the server is running on http://localhost:8000")
    
    try:
        # Test 1: Explanation with Markdown
        session_id = test_explanation_markdown()
        
        if session_id:
            # Test 2: Flowchart with Mermaid (using the session from test 1)
            test_flowchart_mermaid(session_id)
        else:
            print("\n✗ Skipping flowchart test - no valid session")
    
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to server at http://localhost:8000")
        print("Make sure the server is running: python server.py")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
