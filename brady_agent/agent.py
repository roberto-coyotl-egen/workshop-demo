import os
import random
import vertexai
from dotenv import load_dotenv
from google.adk.agents import Agent

# --- 1. SETUP & CREDENTIALS ---
load_dotenv(".env")
    
project_id = os.getenv("GCP_PROJECT_ID")
location = "us-central1"

if project_id:
    vertexai.init(project=project_id, location=location)
else:
    print("❌ Error: GCP_PROJECT_ID missing from .env file")

# --- 2. LOGISTICS TOOLS ---

def track_shipment(shipment_id: str) -> dict:
    """Retrieves real-time status for a shipment (BR-xxxx)."""
    # DEMO FAIL-SAFE: Specific ID for testing "Not Found" observability
    if shipment_id == "BR-0000":
        return {"error": "Shipment ID not found in the global registry."}
        
    locations = ["Port of Los Angeles", "En Route (I-40 East)", "Chicago Hub", "Out for Delivery"]
    contents = ["Electronics Components", "Raw Steel", "Consumer Goods", "Automotive Parts"]
    
    return {
        "shipment_id": shipment_id,
        "status": random.choice(["In Transit", "Delayed", "Customs Hold", "Delivered"]),
        "current_location": random.choice(locations),
        "contents": random.choice(contents),
        "eta": f"{random.randint(1, 5)} days"
    }

def check_inventory(item: str, location: str) -> dict:
    """Checks stock levels for a specific item at a warehouse location."""
    qty = random.randint(0, 5000)
    return {
        "item": item, "location": location, "quantity_on_hand": qty,
        "status": "In Stock" if qty > 500 else "Low Stock",
        "reorder_threshold": 500
    }

def get_truck_maintenance_log(truck_id: str) -> dict:
    """Returns the maintenance history and mileage for a specific truck."""
    return {
        "truck_id": truck_id,
        "current_mileage": random.randint(10000, 250000),
        "last_service_date": "2024-01-15",
        "status": "Active"
    }

# --- 3. AGENT DEFINITION ---
root_agent = Agent(
    name="brady_agent",
    model="gemini-2.5-flash", 
    description="Intelligent Logistics Coordinator for Brady Supply Chain.",
    instruction="""
    You are 'Brady', the AI Logistics Coordinator. 
    
    PROTOCOLS:
    1. **Verify Truth**: If a user mentions a shipment status, ALWAYS call `track_shipment` to verify before agreeing.
    2. **Capability Listing**: When asked what you can do, explicitly state you track shipments using "BR-xxx" IDs.
    3. **Multi-Asset**: If comparing two items, call the relevant tools for BOTH assets before summarizing.
    4. **Actionable**: If inventory is low, proactively offer to draft a restock request.
    """,
    tools=[track_shipment, check_inventory, get_truck_maintenance_log]
)