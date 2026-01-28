import random
from google.adk.agents import Agent
from dotenv import load_dotenv

load_dotenv()

# --- 1. Updated Tools ---
def lookup_order(order_id: str) -> dict:
    """
    Retrieves details for a specific order ID (e.g., ORD-123).
    Returns the status, delivery date, and list of items in the package.
    """
    # Mock Database with Item Details
    mock_db = {
        "ORD-123": {
            "status": "Shipped", 
            "delivery": "Tuesday, Jan 28th",
            "items": ["Wireless Headphones", "Protective Case"]
        },
        "ORD-456": {
            "status": "Pending", 
            "delivery": "TBD",
            "items": ["Gaming Monitor (27 inch)", "HDMI Cable"]
        },
        "ORD-789": {
            "status": "Delivered", 
            "delivery": "Delivered Yesterday",
            "items": ["Coffee Maker", "100x Filters"]
        }
    }
    
    # Return the full dictionary or an error dict
    return mock_db.get(order_id, {"error": "Order ID not found."})

def generate_random_order() -> dict:
    """Generates a random fake order with items."""
    products = ["Laptop", "Mouse", "Keyboard", "Webcam", "Headset"]
    return {
        "order_id": f"ORD-{random.randint(1000, 9999)}",
        "status": random.choice(["Shipped", "Pending"]),
        "items": random.sample(products, 2) # Pick 2 random items
    }

# --- 2. Updated Agent ---
root_agent = Agent(
    name="brady_agent",
    model="gemini-2.5-flash",
    description="Logistics assistant that checks order status and contents.",
    instruction="""
    You are 'Brady', a helpful logistics assistant.
    
    Responsibilities:
    1. **Check Order Details**: Use `lookup_order` to find status AND contents. 
       - If a user asks "What is inside ORD-123?", list the items clearly.
       - If a user asks "Where is ORD-123?", provide the status and delivery date.
    2. **Generate Data**: Use `generate_random_order` for test scenarios.
    
    Tone: Professional and precise.
    """,
    tools=[lookup_order, generate_random_order]
)