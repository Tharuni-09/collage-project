from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable not found.")
    exit(1)


try:
    print(f"Attempting to initialize Gemini client with key: {api_key[:8]}...")
    client = genai.Client(api_key=api_key)

    print("Connection successful. Sending test prompt...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Write 5 resume bullet points for a Fake News Detection project."
    )

    if response.text:
        print("Success! Response received:")
        print(response.text)
except Exception as e:
    print(f"API Call Failed: {str(e)}")