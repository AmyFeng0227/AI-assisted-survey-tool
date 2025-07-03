from dotenv import load_dotenv
from openai import OpenAI
import os

# Initialize OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_survey"))
