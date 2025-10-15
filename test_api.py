
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print("\nTesting /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_explain():
    print("\nTesting /api/explain endpoint...")
    payload = {
        "question": "What is machine learning?",
        "difficulty": "beginner"
    }
    response = requests.post(f"{BASE_URL}/api/explain", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_flashcards():
    print("\nTesting /api/flashcards endpoint...")
    payload = {
        "topic": "Neural Networks",
        "count": 3
    }
    response = requests.post(f"{BASE_URL}/api/flashcards", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_quiz():
    print("\nTesting /api/quiz endpoint...")
    payload = {
        "topic": "Machine Learning Basics",
        "num_questions": 3,
        "difficulty": "medium"
    }
    response = requests.post(f"{BASE_URL}/api/quiz", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_thought_questions():
    print("\nTesting /api/thought-questions endpoint...")
    payload = {
        "topic": "Artificial Intelligence",
        "count": 3
    }
    response = requests.post(f"{BASE_URL}/api/thought-questions", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_topics():
    print("\nTesting /api/topics endpoint...")
    response = requests.get(f"{BASE_URL}/api/topics")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("=" * 60)
    print("AI EXPLAINER BOT API - TESTING")
    print("=" * 60)
    
    try:
        test_health()
        test_topics()
        test_explain()
        print("\n" + "=" * 60)
        print("Basic tests completed!")
        print("=" * 60)
        test_flashcards()
        test_quiz()
        test_thought_questions()
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Make sure the server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"\nError: {e}")
