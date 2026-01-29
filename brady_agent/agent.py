import os
import random
import vertexai
from dotenv import load_dotenv
from google.adk.agents import Agent

# --- 1. SETUP & CREDENTIALS ---
import os
from dotenv import load_dotenv


load_dotenv(".env")
    
project_id = os.getenv("GCP_PROJECT_ID")
location = "us-central1"

if project_id:
    # Initialize Vertex AI globally for the ADK
    vertexai.init(project=project_id, location=location)
else:
    print("❌ Error: GCP_PROJECT_ID missing from .env file")

# --- 2. ENHANCED TOOLS ---
def lookup_order(order_id: str) -> dict:
    """
    Retrieves full details for a specific order ID.
    Returns status, customer info, delivery estimates, tracking links, and itemized lists.
    """
    mock_db = {
        "ORD-123": {
            "status": "Shipped",
            "customer": "Alice Smith",
            "delivery_date": "Tuesday, Jan 28th",
            "tracking_link": "https://shipping.com/track/1Z999",
            "shipping_address": "123 Maple St, New York, NY",
            "items": [
                {"name": "Wireless Headphones", "qty": 1, "price": 150.00},
                {"name": "Protective Case", "qty": 1, "price": 20.00}
            ]
        },
        "ORD-456": {
            "status": "Pending",
            "customer": "Bob Jones",
            "delivery_date": "TBD (Awaiting Stock)",
            "shipping_address": "456 Oak Dr, Austin, TX",
            "items": [
                {"name": "Gaming Monitor (27 inch)", "qty": 1, "price": 300.00},
                {"name": "HDMI Cable (6ft)", "qty": 2, "price": 15.00}
            ]
        },
        "ORD-789": {
            "status": "Delivered",
            "customer": "Charlie Day",
            "delivery_date": "Delivered Yesterday (Front Porch)",
            "proof_of_delivery": "https://img.delivery.com/proof/789.jpg",
            "items": [
                {"name": "Premium Coffee Maker", "qty": 1, "price": 85.00},
                {"name": "Paper Filters (100pk)", "qty": 1, "price": 5.00}
            ]
        }
    }
    
    # Return the data or a standard error
    return mock_db.get(order_id, {"error": "Order ID not found in system."})

def generate_random_order() -> dict:
    """Generates a random fake order with items for testing purposes."""
    products = ["Laptop", "Mouse", "Keyboard", "Webcam", "Headset"]
    return {
        "order_id": f"ORD-{random.randint(1000, 9999)}",
        "status": random.choice(["Shipped", "Pending", "Processing"]),
        "total_value": f"${random.randint(50, 500)}.00",
        "items": random.sample(products, 2)
    }

# --- 3. AGENT DEFINITION ---
root_agent = Agent(
    name="brady_agent",
    model="gemini-2.0-flash",
    description="Logistics assistant that checks order status, contents, and tracking.",
    instruction="""
    You are 'Brady', an advanced logistics assistant.
    
    YOUR RESPONSIBILITIES:
    1. **Detailed Status Checks**: When asked about an order (e.g., ORD-123), use `lookup_order`.
       - **ALWAYS** summarize the:
         - **Status** (e.g., Shipped)
         - **Delivery Date**
         - **Items** inside (be specific!)
       - If available, mention the **Tracking Link** or **Shipping Address** for verification.
    
    2. **Handling Missing Orders**: If `lookup_order` returns an error, politely apologize and ask the user to double-check the ID.
    
    3. **Test Data**: If a user asks for a fake order, use `generate_random_order`.
    
    TONE & STYLE: 
    - Be helpful, concise, and professional.
    - If the user asks "Where is it?", include the tracking link if one exists.
    - If the user asks "What is inside?", list the item names clearly.
    """,
    tools=[lookup_order, generate_random_order]
)