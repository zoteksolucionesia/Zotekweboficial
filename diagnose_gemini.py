import os
from dotenv import load_dotenv
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.services.gemini_service import GeminiEngine

def test_init():
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    print(f"API Key present: {bool(key)}")
    try:
        print("Initializing GeminiEngine...")
        engine = GeminiEngine(api_key=key)
        print("✅ Initialization successful")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_init()
