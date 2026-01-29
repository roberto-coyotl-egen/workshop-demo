import os
from flask import Flask, request, jsonify
# Import your actual agent class here. 
# Adjust 'agent' and 'BradyAgent' to match your actual filename and class name.
from agent import BradyAgent 

app = Flask(__name__)
agent = BradyAgent() # Initialize your agent

@app.route("/", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # Run the agent
    response = agent.chat(user_input) # Adjust this method call to match your agent's API
    
    return jsonify({"response": response})

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    # CRITICAL: Cloud Run expects port 8080 and host 0.0.0.0
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)