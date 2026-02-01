import json, sys, os
import vertexai
from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration, Part

# --- 1. SETUP ---
# Define your acceptable pass rate here (e.g., 80%)
PASS_THRESHOLD = 80 

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
load_dotenv(os.path.join(root_dir, ".env"))

project_id = os.getenv("GCP_PROJECT_ID")
vertexai.init(project=project_id, location="us-central1")

from brady_agent import root_agent

tool_map = {f.__name__: f for f in root_agent.tools}
agent_tools = Tool(function_declarations=[FunctionDeclaration.from_func(f) for f in root_agent.tools])

student_model = GenerativeModel(root_agent.model, system_instruction=root_agent.instruction, tools=[agent_tools])
judge_model = GenerativeModel("gemini-2.5-flash")

# --- 2. EXECUTION ENGINE ---
def execute_turn(chat, prompt):
    """Handles parallel tool calls for complex reasoning cases."""
    try:
        response = chat.send_message(prompt)
        parts = response.candidates[0].content.parts
        function_calls = [p.function_call for p in parts if p.function_call]
        
        if function_calls:
            responses_parts = []
            for fn_call in function_calls:
                fn_name = fn_call.name
                args = dict(fn_call.args)
                print(f"      ⚙️  Tool Call: {fn_name}")
                result = tool_map[fn_name](**args)
                responses_parts.append(Part.from_function_response(name=fn_name, response={"result": result}))
            response = chat.send_message(responses_parts)
            
        return response.text
    except Exception as e:
        return f"System Error: {str(e)}"

def grade(history, criteria):
    prompt = f"QA Judge: Evaluate convo against criteria: {criteria}\nLog:\n{history}\nReply PASS/FAIL + reason."
    return judge_model.generate_content(prompt).text.strip()

# --- 3. MAIN RUNNER ---
def run():
    try:
        cases = json.load(open(os.path.join(root_dir, "tests/dataset.json")))
    except FileNotFoundError:
        print("❌ Dataset missing")
        sys.exit(1)

    print(f"🚀 Evaluating Agent against {len(cases)} cases...")
    score = 0
    
    for test in cases:
        print(f"\n🔹 {test['id']}")
        chat = student_model.start_chat()
        inputs = test['input'] if isinstance(test['input'], list) else [test['input']]
        convo_log = ""
        
        for msg in inputs:
            res = execute_turn(chat, msg)
            convo_log += f"User: {msg}\nAgent: {res}\n"
        
        result = grade(convo_log, test['criteria'])
        if "PASS" in result:
            print("   ✅ PASS")
            score += 1
        else:
            print(f"   ❌ {result}")
    
    final_score = int(score / len(cases) * 100)
    print(f"\n" + "="*30)
    print(f"📊 Final Score: {final_score}% (Threshold: {PASS_THRESHOLD}%)")
    print("="*30)
    
    # Return the score to the shell caller
    return final_score

if __name__ == "__main__":
    actual_score = run()
    if actual_score < PASS_THRESHOLD:
        print("🛑 BUILD REJECTED: Pass rate too low.")
        sys.exit(1)  # Signal failure to Cloud Build
    else:
        print("🎉 BUILD APPROVED.")
        sys.exit(0)  # Signal success to Cloud Build