import os
# import random
import vertexai
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent, ParallelAgent


# --- 1. SETUP & CREDENTIALS ---
load_dotenv(".env")
    
project_id = os.getenv("GCP_PROJECT_ID")
location = "us-central1"
vertexai.init(project=project_id, location=location)


# root_agent = Agent(
#     name="star_wars_quotes",
#     model="gemini-2.5-pro", 
#     description="This agent is a movie nerd that knows every memorable quote from popular movies",
#     instruction="""
#     Respond with the following: 
#     1. What movie or franchise is the quote from. 
#     2. The year the movie was released. 
#     3. What charachter said the quote and to whom.
#     4. Describe the scene in the movie that the quote is from
#     """
# )

# Specialist A: The Fact Checker (Hard Data)
fact_agent = Agent(
    name="fact_checker",
    model="gemini-2.5-pro",
    output_key="generated_fact",
    instruction="""
    You are a precise database. Given a movie quote, identify:
    1. The exact Movie Title or Franchise.
    2. The Release Year.
    3. The Character who said it and to whom.
    
    Output this as a simple list. Do not describe the scene.
    """
)

# Specialist B: The Scene Painter (Creative Data)
scene_agent = Agent(
    name="scene_describer",
    model="gemini-2.5-pro",
    output_key="generated_scene",
    instruction="""
    You are a script supervisor. Given a movie quote, describe the visual context:
    - Where are they standing?
    - What is happening around them?
    - What is the emotional tone?
    
    Do not list the year or actors. Just describe the moment.
    """
)

# Specialist C: The Final Editor (Formatting)
writer_agent = Agent(
    name="final_editor",
    model="gemini-2.5-pro",
    output_key="FINAL_RESPONSE",
    instruction="""
    You are the "Movie Nerd" personality. 
    You will receive two sets of notes (Facts and Scene Description).
    
    Combine {generated_scene} and {generated_fact} them into a single, cohesive response with this exact format:
    
    1. **Movie/Franchise:** [Title]
    2. **Year:** [Year]
    3. **Character:** [Speaker] (talking to [Listener])
    4. **The Scene:** [Insert the vivid scene description here]
    
    Keep the tone enthusiastic but professional.
    """
)

# --- 3. COMPOSE THE AGENTS ---

# Step 1: Run Fact and Scene agents at the same time
research_layer = ParallelAgent(

    name="research_group",
    sub_agents=[fact_agent, scene_agent]
)

# Step 2: Feed the Research into the Writer
root_agent = SequentialAgent(
    name="movie_nerd_pipeline",
    sub_agents=[research_layer, writer_agent]
)

