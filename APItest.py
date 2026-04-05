from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print("✅ API key loaded successfully")
    print(api_key[:10] + "...")  # print only part for safety
else:
    print("❌ API key not found")

