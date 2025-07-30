import os
from supabase import create_client, Client as SupabaseClient
from supabase.client import ClientOptions
from dotenv import load_dotenv
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: SupabaseClient = create_client(url, key)

bucket = supabase.storage.from_("clips")

print(bucket, 'CLIPS BUCKET')

