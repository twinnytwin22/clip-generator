import os
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = "output"
TEMP_DIR = "temp"
INPUT_DIR = "input"

USE_SUPABASE = os.getenv("USE_SUPABASE", "False") == "True"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
