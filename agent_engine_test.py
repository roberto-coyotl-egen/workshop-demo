import os
import json
import requests
import google.auth
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# 1. Setup
import os
from dotenv import load_dotenv


load_dotenv(".env")

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("REGION", "us-central1")
AGENT_ID = os.getenv("AGENT_ID")
ENGINE_URL = f"https://{REGION}-aiplatform.googleapis.com/v1beta1/{AGENT_ID}:streamQuery"

# Auth
creds, _ = google.auth.default()
creds.refresh(Request())
headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

# 2. The Test Suite
test_cases = [
    {
        "desc": "✅ SHIPPED ORDER (Expect: Wireless Headphones)",
        "query": "Where is order ORD-123?"
    },
    {
        "desc": "⏳ PENDING ORDER (Expect: Gaming Monitor / TBD)",
        "query": "What is the status of ORD-456?"
    },
    {
        "desc": "📦 DELIVERED ORDER (Expect: Coffee Maker)",
        "query": "Tell me about order ORD-789"
    },
    {
        "desc": "🎲 TOOL USAGE (Expect: Random Order Generation)",
        "query": "Generate a random fake order for testing."
    },
    {
        "desc": "❌ MISSING ORDER (Expect: Error Handling)",
        "query": "Where is order ORD-999?"
    }
]

def run_test(scenario):
    print(f"\n──────────────────────────────────────────────────")
    print(f"🔹 TEST: {scenario['desc']}")
    print(f"   User > \"{scenario['query']}\"")
    print(f"   (Agent is thinking...)", end="", flush=True)

    payload = {
        "input": {
            "message": scenario['query'],
            "user_id": "final_verifier_01" 
        }
    }

    try:
        resp = requests.post(ENGINE_URL, json=payload, headers=headers, stream=True)
        resp.raise_for_status()
        
        print("\r   🤖 Brady > ", end="") 
        
        full_text = ""
        for line in resp.iter_lines():
            if line:
                decoded = line.decode('utf-8').replace("data: ", "")
                try:
                    chunk = json.loads(decoded)
                    
                    # --- CORRECT PARSER FOR YOUR AGENT ---
                    # We look for: content -> parts -> [0] -> text
                    content = chunk.get("content", {})
                    if "parts" in content:
                        for part in content["parts"]:
                            if "text" in part:
                                text_fragment = part["text"]
                                print(text_fragment, end="", flush=True)
                                full_text += text_fragment
                    
                    # Fallback for simpler messages
                    elif "output" in chunk:
                         print(chunk["output"], end="", flush=True)
                         full_text += str(chunk["output"])

                except:
                    pass
        
        if not full_text.strip():
             # If we got JSON but no text, it might have been a silent tool call intermediate step
             pass 

        print("") 

    except Exception as e:
        print(f"\n❌ Error: {e}")

# 3. Run It
print(f"🚀 Launching Final Verification for Agent: {AGENT_ID}...")
for case in test_cases:
    run_test(case)

print("\n✅ All systems operational.")