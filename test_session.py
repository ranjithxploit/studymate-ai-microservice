"""
Test script for Session Management functionality
Tests UUID-based sessions, context storage, history tracking, and PDF uploads
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_create_session():
    """Test creating a new session"""
    print_section("TEST 1: Create New Session")
    
    response = requests.post(f"{BASE_URL}/api/session/create")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        session_id = data["session_id"]
        print(f"✅ Session created successfully!")
        print(f"Session ID: {session_id}")
        print(f"Created at: {data['created_at']}")
        return session_id
    else:
        print(f"❌ Failed to create session: {response.text}")
        return None

def test_explain_with_session(session_id):
    """Test explain endpoint with session tracking"""
    print_section("TEST 2: Explain Concept with Session")
    
    payload = {
        "question": "What is neural network?",
        "difficulty": "beginner",
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/api/explain", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Explanation generated!")
        print(f"Session ID: {data['session_id']}")
        print(f"Question: {data['question']}")
        print(f"Explanation: {data['explanation'][:100]}...")
        print(f"Example: {data['example'][:100]}...")
        return data['session_id']
    else:
        print(f"❌ Failed: {response.text}")
        return session_id

def test_explain_without_session():
    """Test explain endpoint without session (auto-create)"""
    print_section("TEST 3: Explain Without Session (Auto-create)")
    
    payload = {
        "question": "What is machine learning?",
        "difficulty": "beginner"
    }
    
    response = requests.post(f"{BASE_URL}/api/explain", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Auto-created session!")
        print(f"Session ID: {data['session_id']}")
        print(f"Explanation: {data['explanation'][:100]}...")
        return data['session_id']
    else:
        print(f"❌ Failed: {response.text}")
        return None

def test_get_session_history(session_id):
    """Test retrieving session history"""
    print_section("TEST 4: Get Session History")
    
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/history")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ History retrieved!")
        print(f"Session ID: {data['session_id']}")
        print(f"Message Count: {data['message_count']}")
        print(f"\nHistory entries:")
        for i, entry in enumerate(data['history'], 1):
            print(f"\n  {i}. Type: {entry.get('type', 'unknown')}")
            print(f"     Time: {entry.get('timestamp', 'unknown')}")
            print(f"     Input: {entry.get('user_input', '')[:50]}...")
    else:
        print(f"❌ Failed: {response.text}")

def test_get_session_context(session_id):
    """Test retrieving session context"""
    print_section("TEST 5: Get Session Context")
    
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/context")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Context retrieved!")
        print(f"Session ID: {data['session_id']}")
        print(f"Context:\n{data['context'][:200]}...")
    else:
        print(f"❌ Failed: {response.text}")

def test_get_session_metadata(session_id):
    """Test retrieving session metadata"""
    print_section("TEST 6: Get Session Metadata")
    
    response = requests.get(f"{BASE_URL}/api/session/{session_id}/metadata")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Metadata retrieved!")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Failed: {response.text}")

def test_list_sessions():
    """Test listing all sessions"""
    print_section("TEST 7: List All Sessions")
    
    response = requests.get(f"{BASE_URL}/api/sessions")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sessions listed!")
        print(f"Total sessions: {data['total_count']}")
        print(f"\nFirst 3 sessions:")
        for i, session in enumerate(data['sessions'][:3], 1):
            print(f"\n  {i}. Session ID: {session['session_id']}")
            print(f"     Created: {session.get('created_at', 'unknown')}")
            print(f"     Messages: {session.get('message_count', 0)}")
    else:
        print(f"❌ Failed: {response.text}")

def test_flashcards_with_session(session_id):
    """Test flashcards with session"""
    print_section("TEST 8: Generate Flashcards with Session")
    
    payload = {
        "topic": "Deep Learning",
        "count": 3,
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/api/flashcards", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Flashcards generated!")
        print(f"Session ID: {data['session_id']}")
        print(f"Topic: {data['topic']}")
        print(f"Number of flashcards: {len(data['flashcards'])}")
        for i, card in enumerate(data['flashcards'][:2], 1):
            print(f"\n  Card {i}:")
            print(f"    Front: {card['front']}")
            print(f"    Back: {card['back'][:50]}...")
    else:
        print(f"❌ Failed: {response.text}")

def test_create_pdf_for_upload():
    """Create a dummy PDF file for testing"""
    pdf_path = Path("test_input.pdf")
    
    # Create a simple PDF-like file (for testing purposes)
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n')
        f.write(b'%Test PDF content for session testing\n')
        f.write(b'This is a test PDF file.\n')
        f.write(b'%%EOF\n')
    
    return pdf_path

def test_upload_pdf(session_id):
    """Test PDF upload to session"""
    print_section("TEST 9: Upload PDF to Session")
    
    # Create test PDF
    pdf_path = test_create_pdf_for_upload()
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test_input.pdf', f, 'application/pdf')}
            response = requests.post(
                f"{BASE_URL}/api/session/{session_id}/upload-pdf",
                files=files
            )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PDF uploaded successfully!")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Failed: {response.text}")
    
    finally:
        # Cleanup
        if pdf_path.exists():
            pdf_path.unlink()

def test_delete_session(session_id):
    """Test deleting a session"""
    print_section("TEST 10: Delete Session")
    
    response = requests.delete(f"{BASE_URL}/api/session/{session_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session deleted!")
        print(f"Message: {data['message']}")
    else:
        print(f"❌ Failed: {response.text}")

def main():
    """Run all session tests"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     AI EXPLAINER BOT - SESSION MANAGEMENT TESTS          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    try:
        # Test 1: Create session
        session_id = test_create_session()
        if not session_id:
            print("\n❌ Cannot continue without a session ID")
            return
        
        # Test 2: Use session with explain endpoint
        session_id = test_explain_with_session(session_id)
        
        # Test 3: Auto-create session
        new_session_id = test_explain_without_session()
        
        # Test 4-6: Session retrieval
        test_get_session_history(session_id)
        test_get_session_context(session_id)
        test_get_session_metadata(session_id)
        
        # Test 7: List all sessions
        test_list_sessions()
        
        # Test 8: Generate flashcards with session
        test_flashcards_with_session(session_id)
        
        # Test 9: Upload PDF
        test_upload_pdf(session_id)
        
        # Check context files exist
        print_section("VERIFY: Check Session Files")
        context_dir = Path("context") / session_id
        if context_dir.exists():
            print(f"✅ Session directory exists: {context_dir}")
            for file in context_dir.iterdir():
                print(f"  📄 {file.name} ({file.stat().st_size} bytes)")
        else:
            print(f"❌ Session directory not found: {context_dir}")
        
        # Test 10: Delete session (optional - uncomment to test)
        # test_delete_session(new_session_id)
        
        print_section("ALL TESTS COMPLETED!")
        print(f"\n💡 Your main session ID: {session_id}")
        print(f"📁 Session files are in: context/{session_id}/")
        print(f"\nYou can continue using this session ID in your API calls!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("Make sure the server is running on http://127.0.0.1:8000")
        print("\nStart the server with:")
        print("  python -m uvicorn server:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
