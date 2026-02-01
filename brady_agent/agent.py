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

# --- 2. LOGISTICS TOOLS (Expanded for Demo) ---

def track_shipment(shipment_id: str) -> dict:
    """
    Retrieves real-time status for a shipment (BR-xxxx).
    Includes current location, container contents, and estimated arrival.
    """
    # Simulate a realistic database lookup
    locations = ["Port of Los Angeles", "En Route (I-40 East)", "Chicago Distribution Center", "Out for Delivery"]
    contents = ["Electronics Components", "Raw Steel", "Consumer Goods (Perishable)", "Automotive Parts"]
    
    # Randomly generate details to support the high-volume demo
    return {
        "shipment_id": shipment_id,
        "status": random.choice(["In Transit", "Delayed - Weather", "Customs Hold", "Delivered"]),
        "current_location": random.choice(locations),
        "contents": random.choice(contents),
        "eta": f"{random.randint(1, 5)} days",
        "last_updated": "2 hours ago"
    }

def check_inventory(item: str, location: str) -> dict:
    """
    Checks stock levels for a specific item at a specific warehouse location.
    """
    qty = random.randint(0, 5000)
    status = "In Stock" if qty > 500 else "Low Stock" if qty > 0 else "Out of Stock"
    
    return {
        "item": item,
        "location": location,
        "quantity_on_hand": qty,
        "status": status,
        "reorder_threshold": 500
    }

def get_truck_maintenance_log(truck_id: str) -> dict:
    """
    Returns the maintenance history and mileage for a specific truck.
    Useful for comparing fleet assets.
    """
    mileage = random.randint(10000, 250000)
    last_service = random.choice(["Oil Change", "Brake Replacement", "Tire Rotation", "Engine Tune-up"])
    
    return {
        "truck_id": truck_id,
        "current_mileage": mileage,
        "last_service_date": "2024-01-15",
        "last_service_type": last_service,
        "status": "Active" if mileage < 200000 else "Needs Review"
    }

# --- 3. AGENT DEFINITION ---
root_agent = Agent(
    name="brady_agent",
    # We use Gemini 2.5 Pro for its excellent reasoning and tool-calling speed
    model="gemini-2.5-pro",
    description="Intelligent Logistics Coordinator for Brady Supply Chain.",
    instruction="""
    You are 'Brady', the AI Logistics Coordinator. Your goal is to assist drivers, warehouse managers, and executives with supply chain visibility.

    YOUR CAPABILITIES:
    1. **Shipment Tracking**: Use `track_shipment` for any ID starting with "BR-".
       - If the status is "Delayed", always apologize and suggest notifying the customer.
       - Always mention the specific contents of the container.

    2. **Inventory Management**: Use `check_inventory` when users ask about stock levels in specific cities.
       - If stock is "Low" or "Out", proactively suggest drafting a restocking order.

    3. **Fleet Maintenance**: Use `get_truck_maintenance_log` to compare trucks.
       - If a user asks to compare two trucks, call the tool twice (once for each truck) and then summarize which one has higher mileage.

    4. **General Assistance**:
       - If a user just says "Hello" or "Shift change", be professional and concise (e.g., "Ready for the new shift. What do you need?").
       - If a user provides a bad ID (like "INVALID" or "NULL"), polite explain that the format is incorrect.

    TONE:
    - Professional, efficient, and data-driven.
    - For "Exec" personas, be brief. For "Driver" personas, be clear and direct.
    """,
    # Registering ALL tools so the agent can handle the diverse traffic
    tools=[track_shipment, check_inventory, get_truck_maintenance_log]
)