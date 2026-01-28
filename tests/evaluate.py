import json, sys, os
import vertexai
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration, Part

# --- 1. SETUP & CREDENTIALS ---
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
load_dotenv(os.path.join(root_dir, ".env"))

project_id = os.getenv("GCP_PROJECT_ID")
if not project_id:
    sys.exit("❌ Missing GCP_PROJECT_ID in .env")

# Initialize Vertex AI globally
vertexai.init(project=project_id, location="us-central1")

# Import Agent AFTER init
from brady_agent import root_agent

# --- 2. BUILD MODELS ---
# Prepare Tools for the Student
tool_map = {f.__name__: f for f in root_agent.tools}
agent_tools = Tool(function_declarations=[FunctionDeclaration.from_func(f) for f in root_agent.tools])

# Student: The Agent being tested
student_model = GenerativeModel(
    root_agent.model, 
    system_instruction=root_agent.instruction, 
    tools=[agent_tools]
)

# Judge: The Evaluator (Gemini 2.0)
judge_model = GenerativeModel("gemini-2.5-flash")

# --- 3. HELPER FUNCTIONS ---

def execute_turn(chat, prompt):
    """
    Sends a message to the chat session and handles any tool calls automatically.
    Returns the final text response from the agent.
    """
    try:
        response = chat.send_message(prompt)
        
        # Check if the model wants to call a tool
        part = response.candidates[0].content.parts[0]
        
        if part.function_call:
            fn_name = part.function_call.name
            args = dict(part.function_call.args)
            print(f"      ⚙️  Tool Call: {fn_name}")
            
            try:
                # Run the actual Python function
                result = tool_map[fn_name](**args)
            except Exception as e:
                result = f"Tool Error: {str(e)}"
            
            # Send the tool output back to the model
            response = chat.send_message(
                Part.from_function_response(name=fn_name, response={"result": result})
            )
            
        return response.text
    except Exception as e:
        return f"System Error: {str(e)}"

def grade(history, criteria):
    """
    Asks the Judge model to evaluate the entire conversation history 
    against the specific success criteria.
    """
    prompt = f"""
    You are a QA Judge. Evaluate this conversation.
    
    --- CONVERSATION LOG ---
    {history}
    
    --- SUCCESS CRITERIA ---
    {criteria}
    
    --- TASK ---
    Did the Agent meet the criteria? 
    Strictly reply with 'PASS' or 'FAIL', followed by a short reason.
    """
    return judge_model.generate_content(prompt).text.strip()

# --- 4. MAIN TEST LOOP ---

def run():
    # Load the test cases
    try:
        cases = json.load(open(os.path.join(root_dir, "tests/dataset.json")))
    except FileNotFoundError:
        sys.exit("❌ dataset.json not found.")

    print(f"🚀 Running {len(cases)} Tests (Multi-Turn Supported)...")
    
    score = 0
    
    for test in cases:
        print(f"\n🔹 Test [{test['id']}]")
        
        # Start a NEW chat session for every test (clears memory)
        chat = student_model.start_chat()
        
        # Normalize input: If string, make it a list. If list, keep it.
        inputs = test['input'] if isinstance(test['input'], list) else [test['input']]
        
        conversation_log = ""
        
        # Run through every turn in the conversation
        for i, user_msg in enumerate(inputs):
            print(f"   User ({i+1}): {user_msg}")
            
            # Execute the turn
            agent_response = execute_turn(chat, user_msg)
            
            # Clean up response for display
            display_response = agent_response.replace('\n', ' ')[:60]
            print(f"   Agent:   {display_response}...")
            
            # Append to history log for the Judge
            conversation_log += f"User: {user_msg}\nAgent: {agent_response}\n"

        # Judge the final result
        result = grade(conversation_log, test['criteria'])
        
        if "PASS" in result:
            print("   ✅ PASS")
            score += 1
        else:
            print(f"   ❌ FAIL: {result}")
    
    # Final Report
    final_score = int(score / len(cases) * 100)
    print(f"\n" + "="*30)
    print(f"📊 Final Score: {final_score}%")
    print("="*30)
    
    # Exit with error code if not perfect (for CI/CD)
    if final_score < 100:
        sys.exit(1)

if __name__ == "__main__":
    run()