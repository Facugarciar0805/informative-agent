import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.gemini import GeminiModel

load_dotenv()

model = GeminiModel(
    client_args={"api_key": os.environ["GEMINI_API_KEY"]},
    model_id="gemini-3.6-flash"
)

agent = Agent(model=model)


