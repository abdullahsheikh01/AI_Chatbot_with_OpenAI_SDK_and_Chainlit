# Imports
import os # To get environment variable
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig, Agent, Runner # Open AI Agents SDK(Imports)
import chainlit as cl # Chainlit(Frontend)
from dotenv import load_dotenv # To load Environment Variables
from openai.types.responses import ResponseTextDeltaEvent

# Environment Variables loading 
load_dotenv()

# Getting API Key of Open Router
API_KEY : str = os.getenv("API_KEY") 

# API_KEY Check Condition
if not API_KEY:
    raise ValueError("API Key is not present!. It should be there")

# Defining an external client
external_client = AsyncOpenAI(
    api_key = API_KEY,
    base_url = "https://openrouter.ai/api/v1"
)

# Defining a model
model = OpenAIChatCompletionsModel(
    model = "deepseek/deepseek-r1-0528:free",
    openai_client = external_client
)

# Making Config to pass in Runner
config = RunConfig(
    model = model,
    model_provider = external_client,
    tracing_disabled = True
)

# Making an agent which responds user prompts
agent : Agent = Agent(
    name = "AI Assistant Chatbot", # Giving a name to agent
    # Instruction given to become polite and helpful assistant chatbot.
    instructions = """You are a kind, polite, and helpful assistant. 
    Your primary goal is to provide clear, easy-to-understand answers.
    Always use simple, everyday language, avoiding jargon or complex terms.
    Be patient and empathetic in your responses.
    Maintain a consistently friendly and approachable tone.
    If you don't know an answer, politely state that you cannot provide the information and offer to assist in another way if possible.
    Keep your responses concise and to the point, but ensure they are complete.
    Before answering, briefly consider the user's likely understanding level.""",
    model = model # Defining a model(Brain) of an agent
)

@cl.on_chat_start # This decorator defines that this function will work whenever new chat starts
async def handle_start_chat():
    cl.user_session.set("chat_history",[]) # Seeting(Here creating) a session variable to track history of conversation
    await cl.Message(content="Welcome to AI Chatbot Agent created by Abdullah Shaikh").send() # Welcome Message

@cl.on_message # This defines this function will work message send by user
async def main(message:cl.Message):
    # Try Except Conditions to handle error in the case of Errors
    try:
        chat_history = cl.user_session.get("chat_history")
        chat_history.append({"role":"user","content":message.content})
        # Running an agent
        result = Runner.run_streamed( # It runs agent
        agent, # Agent defined to run
        chat_history, # Prompt Given which was given by user
        run_config=config # Give it config for running(working) of agent
    )
        msg = cl.Message(content="") # Empty Message Send First to use this object
        await msg.send()
        for _ in ["Agent ","Start ", "to ", "think🤔....\n"]:
            await msg.stream_token(_) # Use this as a magical output for user
        async for event in result.stream_events(): # async loop to get tokens
            if event.type=="raw_response_event" and hasattr(event.data,"delta") and isinstance(event.data,  ResponseTextDeltaEvent):
                token = event.data.delta # Tokens store there
                await msg.stream_token(token) # Here each token send to the user in each iteration as message but they all are combined as single message
        chat_history.append({"role":"assistant","content":msg.content})
        cl.user_session.set("chat_history",chat_history) 
        
    # Exception to handle errors 
    except Exception as e:
        print(f"This Error Occured: {e}")
