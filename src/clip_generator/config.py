import os
from dotenv import load_dotenv
from moviepy.config import change_settings

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(INPUT_DIR, exist_ok=True)

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Supabase and OpenAI configuration
USE_SUPABASE = os.getenv("USE_SUPABASE", "False") == "True"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")

# Configure ImageMagick binary for MoviePy
# IMAGEMAGICK_BINARY = os.getenv("IMAGEMAGICK_BINARY", "/usr/local/bin/magick")  # Default path for macOS
# change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})

# Create a settings object for easier access in other modules
class Settings:
    def __init__(self):
        for key, value in globals().items():
            if key.isupper():
                setattr(self, key, value)

settings = Settings()