import json, sys, os
import vertexai
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration, Part

# --- 1. SETUP ENV FIRST ---
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
load_dotenv(os.path.join(root_dir, ".env"))

project_id = os.getenv("GCP_PROJECT_ID")
if not project_id:
    sys.exit("❌ Missing GCP_PROJECT_ID in .env")

# --- 2. LOG IN TO GOOGLE (BEFORE IMPORTING AGENT) ---
# This must happen BEFORE the agent tries to start up
vertexai.init(project=project_id, location="us-central1")

# --- 3. NOW IMPORT THE AGENT ---
from brady_agent import root_agent 

# --- Build Student (Agent) ---
tool_map = {f.__name__: f for f in root_agent.tools}
agent_tools = Tool(function_declarations=[FunctionDeclaration.from_func(f) for f in root_agent.tools])
student_model = GenerativeModel(root_agent.model, system_instruction=root_agent.instruction, tools=[agent_tools])

# --- Build Judge (Evaluator) ---
judge_model = GenerativeModel("gemini-2.0-flash")

# ... (The rest of your script stays exactly the same) ...

def execute_agent(chat, prompt):
    """Runs the agent, executing tools if requested."""
    try:
        response = chat.send_message(prompt)
        part = response.candidates[0].content.parts[0]
        
        if part.function_call:
            fn_name = part.function_call.name
            print(f"   ⚙️  Running Tool: {fn_name}...")
            
            try:
                result = tool_map[fn_name](**dict(part.function_call.args))
            except Exception as tool_err:
                result = f"Tool Error: {str(tool_err)}"
            
            response = chat.send_message(
                Part.from_function_response(name=fn_name, response={"result": result})
            )
            
        return response.text

    except Exception as e:
        return f"System Error: {str(e)}"

def grade(question, answer, criteria):
    prompt = f"Question: {question}\nAnswer: {answer}\nCriteria: {criteria}\n\nStrictly PASS or FAIL with reason."
    return judge_model.generate_content(prompt).text.strip()

def run():
    try:
        cases = json.load(open(os.path.join(root_dir, "tests/dataset.json")))
    except FileNotFoundError:
        sys.exit("❌ dataset.json not found in tests/ folder.")

    print(f"🚀 Running {len(cases)} Tests...")
    
    score = 0
    for test in cases:
        print(f"🔹 [{test['id']}] {test['input']}")
        # Start a fresh chat for every test
        chat = student_model.start_chat()
        answer = execute_agent(chat, test['input'])
        result = grade(test['input'], answer, test['criteria'])
        
        if "PASS" in result:
            print("   ✅ PASS")
            score += 1
        else:
            print(f"   ❌ FAIL: {result}\n   Agent said: {answer}")
    
    print(f"\n📊 Score: {int(score/len(cases)*100)}%")

if __name__ == "__main__":
    run()