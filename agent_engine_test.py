import os
import json
import time
import random
import uuid  # Added for session tracking
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

ENGINE_URL = f"https://{REGION}-aiplatform.googleapis.com/v1beta1/{AGENT_ID}:streamQuery"

USERS = ["Logistics_Mgr_Bob", "Driver_Dave", "Support_Alice", "Warehouse_Steve", "Exec_Sarah"]

# 2. TEST SCENARIOS (Modified for Multi-Turn)
test_cases = []

# [A] 10x Standard Tracking (Single Turn - Fast Volume)
for i in range(101, 111):
    test_cases.append({
        "desc": f"🚚 Tracking Shipment BR-{i}",
        "turns": [f"Where is shipment BR-{i} right now?"], # List of 1
        "user": random.choice(USERS),
        "type": "tracking"
    })

# [B] 5x Inventory Drill-Down (MULTI-TURN: Check -> Detail -> Action)
# This creates "long" sessions in your logs
items = ["Widgets", "Microchips", "Steel Beams", "Tires", "Avocados"]
for item in items:
    city = random.choice(["New York", "Chicago", "Miami"])
    test_cases.append({
        "desc": f"📦 Inventory Drill-Down: {item}",
        "turns": [
            f"Check inventory levels for {item} in {city}.",
            "How does that compare to last month?",
            "Okay, draft a restocking order for me."
        ],
        "user": "Warehouse_Steve",
        "type": "multi_turn_inventory"
    })

# [C] 5x Context Switching (MULTI-TURN: Truck A -> Truck B -> Compare)
# This proves the agent has "Memory"
for i in range(5):
    t1 = random.randint(100, 400)
    t2 = random.randint(500, 900)
    test_cases.append({
        "desc": f"🔧 Maintenance Compare: Truck {t1} vs {t2}",
        "turns": [
            f"Show me the maintenance logs for Truck {t1}.",
            f"Actually, look at Truck {t2} instead.",
            "Which of those two has higher mileage?"
        ],
        "user": "Driver_Dave",
        "type": "multi_turn_reasoning"
    })

# [D] 10x Edge Cases (Single Turn)
bad_ids = ["INVALID-99", "NULL", "undefined", "BR-0000", "???"]
for bid in bad_ids * 2:
    test_cases.append({
        "desc": f"⚠️ Error Injection: {bid}",
        "turns": [f"Status of shipment {bid}"],
        "user": "Support_Alice",
        "type": "error_test"
    })

# [E] 5x Shift Change Chat (MULTI-TURN: Greeting -> Task -> End)
for i in range(5):
    test_cases.append({
        "desc": "💬 Shift Handoff Chat",
        "turns": [
            "Hello, I'm starting my shift.",
            "Are there any urgent alerts?",
            "Thanks, logging off now."
        ],
        "user": "Logistics_Mgr_Bob",
        "type": "chat"
    })

random.shuffle(test_cases)

def run_test(scenario, index, total):
    # Generate a unique Session ID for this entire scenario (Scenario = 1 User Session)
    session_id = f"sess-{uuid.uuid4().hex[:8]}"
    
    print(f"\n[{index}/{total}] ──────────────────────────────────────────")
    print(f"🔹 {scenario['desc']}")
    print(f"   👤 User: {scenario['user']}")
    print(f"   🆔 Session: {session_id}")

    # Authenticate
    creds, _ = google.auth.default()
    creds.refresh(Request())
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    # Loop through the turns (Whether it's 1 question or 3)
    for turn_idx, query in enumerate(scenario['turns']):
        print(f"   ➡️ Turn {turn_idx + 1}: \"{query}\"")
        
        payload = {
            "input": {
                "message": query,
                "user_id": scenario['user'],
                "session_id": session_id  # <--- PASSING CONTEXT HERE
            }
        }

        start_time = time.time()
        
        try:
            resp = requests.post(ENGINE_URL, json=payload, headers=headers, stream=True)
            resp.raise_for_status()
            
            full_text = ""
            print("      🤖 ", end="", flush=True)
            
            for line in resp.iter_lines():
                if line:
                    decoded = line.decode('utf-8').replace("data: ", "")
                    try:
                        chunk = json.loads(decoded)
                        if "output" in chunk:
                            text = str(chunk["output"])
                            print(text, end="", flush=True)
                            full_text += text
                        elif "content" in chunk and "parts" in chunk["content"]:
                             for part in chunk["content"]["parts"]:
                                 if "text" in part:
                                     print(part["text"], end="", flush=True)
                                     full_text += part["text"]
                    except:
                        pass
            
            duration = time.time() - start_time
            print(f"\n      ⏱️  {duration:.2f}s")
            
            # Shorter sleep between turns in the same conversation
            time.sleep(1.0)

        except Exception as e:
            print(f"\n      ❌ Error: {e}")

# 4. EXECUTION LOOP
print(f"🚀 Starting Multi-Turn Observability Gen: {len(test_cases)} Sessions")
print(f"🎯 Target Agent: {AGENT_ID}")
print("────────────────────────────────────────────────────────")

for i, case in enumerate(test_cases):
    run_test(case, i+1, len(test_cases))
    
    # Longer sleep between distinct users/sessions
    time.sleep(random.uniform(1.5, 3.0))

print("\n✅ Traffic Generation Complete.")