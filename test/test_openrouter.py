import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file
load_dotenv()

openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_url = os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
# Let's test using a free model
test_model = "meta-llama/llama-3.3-70b-instruct:free"

print("--- OpenRouter Connection Test ---")
print(f"Base URL: {openrouter_url}")
print(f"API Key: {openrouter_key[:10]}...{openrouter_key[-5:] if openrouter_key else ''}")
print(f"Test Model: {test_model}\n")

if not openrouter_key:
    print("[Error] OPENROUTER_API_KEY is not defined in .env")
    exit(1)

try:
    print("Initializing client...")
    client = OpenAI(
        api_key=openrouter_key,
        base_url=openrouter_url,
        default_headers={
            "HTTP-Referer": "https://localhost:3000",
            "X-Title": "Testing Connection",
        }
    )

    print("Sending chat completion request...")
    response = client.chat.completions.create(
        model=test_model,
        messages=[
            {"role": "user", "content": "Say 'OpenRouter is working!' in exactly 5 words."}
        ]
    )

    print("\n[SUCCESS] OpenRouter responded successfully!")
    print(f"Answer: {response.choices[0].message.content}")

except Exception as e:
    print(f"\n[FAILURE] Connection failed with error: {e}")
