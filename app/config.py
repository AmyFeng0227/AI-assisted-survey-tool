from dotenv import load_dotenv
from openai import OpenAI
import os

# Initialize OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_survey"))
model="o4-mini-2025-04-16"

# Chunking Settings
n_sentences = 20
n_overlap = 2