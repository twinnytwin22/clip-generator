import os
from typing import Optional
from supabase import create_client, Client as SupabaseClient
from dotenv import load_dotenv

load_dotenv()

url: Optional[str] = os.environ.get("SUPABASE_URL")
key: Optional[str] = os.environ.get("SUPABASE_KEY")

supabase: Optional[SupabaseClient] = None

if url and key:
    supabase = create_client(url, key)

