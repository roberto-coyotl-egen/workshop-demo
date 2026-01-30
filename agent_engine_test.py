import os
import json
import time
import uuid
import requests
import google.auth
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# 1. Setup
load_dotenv(".env")

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("REGION", "us-central1")
AGENT_ID = os.getenv("AGENT_ID")

if not AGENT_ID:
    raise ValueError("❌ AGENT_ID is missing from .env")

# The endpoint for streaming interactions
ENGINE_URL = f"https://{REGION}-aiplatform.googleapis.com/v1beta1/{AGENT_ID}:streamQuery"

# 2. DEFINING THE CONVERSATIONS
# Each "scenario" is a list of turns. We expect the agent to remember Turn 1 when answering Turn 2.
conversations = [
    {
        "name": "🚚 The 'Drill Down' (Tracking -> Detail -> ETA)",
        "user": "Logistics_Mgr_Bob",
        "turns": [
            "Where is shipment BR-9901?",
            "What is specifically inside that container?",
            "Is it going to be late?",
            "Okay, email the customer about the delay."
        ]
    },
    {
        "name": "🔧 The 'Context Switch' (Maintenance -> History -> Comparison)",
        "user": "Mechanic_Mike",
        "turns": [
            "Show me the maintenance logs for Truck 402.",
            "Who was the last driver?",
            "Wait, actually check Truck 505 instead.",
            "Which of those two trucks has higher mileage?"
        ]
    },
    {
        "name": "📉 The 'Analyst' (Data -> Summary -> Formatting)",
        "user": "Analyst_Sarah",
        "turns": [
            "How many shipments were delivered to Austin last month?",
            "Break that down by product type.",
            "Can you format that as a bulleted list?",
            "Thanks, that's all."
        ]
    },
    {
        "name": "⚠️ The 'Correction' (Ambiguity -> Refinement)",
        "user": "Support_Alice",
        "turns": [
            "Status of order 123.",
            "Sorry, I meant shipment BR-123, not the order.",
            "Does it have any hazardous materials?",
            "What is the emergency contact for that?"
        ]
    }
]

def run_conversation_thread(conversation):
    # 1. Generate a unique Session ID for this entire thread
    session_id = f"sess-{uuid.uuid4().hex[:8]}"
    user_id = conversation["user"]
    
    print(f"\n🔵 STARTING THREAD: {conversation['name']}")
    print(f"   🆔 Session ID: {session_id}")
    print(f"   👤 User: {user_id}")
    print("   ──────────────────────────────────────────────────")

    # Refresh auth once per thread
    creds, _ = google.auth.default()
    creds.refresh(Request())
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    for i, user_text in enumerate(conversation["turns"]):
        print(f"\n   [{i+1}/{len(conversation['turns'])}] User > \"{user_text}\"")
        
        # 2. The Payload: CRITICAL -> We pass 'session_id' to maintain context
        payload = {
            "input": {
                "message": user_text,
                "user_id": user_id,
                "session_id": session_id # <-- The key to multi-turn memory
            }
        }

        # 3. Fire the request
        try:
            start_time = time.time()
            resp = requests.post(ENGINE_URL, json=payload, headers=headers, stream=True)
            resp.raise_for_status()

            print("   🤖 Brady > ", end="", flush=True)
            
            full_response = ""
            for line in resp.iter_lines():
                if line:
                    decoded = line.decode('utf-8').replace("data: ", "")
                    try:
                        chunk = json.loads(decoded)
                        # Parsing logic (handles standard Gemini/Vertex chunks)
                        if "output" in chunk:
                            text = str(chunk["output"])
                            print(text, end="", flush=True)
                            full_response += text
                        elif "content" in chunk and "parts" in chunk["content"]:
                             for part in chunk["content"]["parts"]:
                                 if "text" in part:
                                     print(part["text"], end="", flush=True)
                                     full_response += part["text"]
                    except:
                        pass
            
            print(f"\n   ⏱️  ({time.time() - start_time:.2f}s)")
            
            # Short sleep to simulate reading time (and avoid rate limits)
            time.sleep(1.5)

        except Exception as e:
            print(f"\n   ❌ Error on turn {i+1}: {e}")
            break # Stop this thread if it crashes

    print(f"   🏁 Thread Complete.\n")

# 3. EXECUTION
print(f"🚀 Starting Multi-Turn Conversation Tests...")
print(f"🎯 Target Agent: {AGENT_ID}")

for convo in conversations:
    run_conversation_thread(convo)
    time.sleep(2) # Pause between different users

print("\n✅ All conversations finished. Check 'Session History' in Vertex AI.")