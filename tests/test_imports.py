from pathlib import Path
from schemas.poll_schema import PollCreate,PollResponse
import sys


current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

print("Python path:", sys.path)
print("Current directory:", current_dir)

try:
    print("Trying to import...")
    from schemas.poll_schema import PollCreate
    print("Import successful!")
    
    test_data = {
        "title": "Test",
        "description": "Test Description",
        "options": [{"text": "Option 1"}]
    }
    
    poll = PollCreate(**test_data)
    print("Object created successfully!")
    print(f"Poll: {poll}")
    
except Exception as e:
    print(f"Error occurred: {type(e).__name__}")
    print(f"Error message: {str(e)}")