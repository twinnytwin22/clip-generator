import os
from utils.supabaseClient.supabase import supabase

def save_srt_to_supabase(project_id: str, profile_id: str, srt_content: str) -> str:
    """
    Save the SRT content to Supabase storage.

    Args:
        project_id (str): ID of the project in Supabase.
        profile_id (str): Profile ID for organizing files.
        srt_content (str): SRT content to save.

    Returns:
        str: Path to the saved SRT file in Supabase storage.
    """
    srt_filename = f"{profile_id}/{project_id}.srt"
    bucket_name = "transcripts"
    temp_file_path = f"/tmp/{project_id}.srt"  # Save the SRT file temporarily

    try:
        # Generate a signed upload URL
               # Generate a signed upload URL
        signed_upload_url = supabase.storage.from_(bucket_name).create_signed_upload_url(srt_filename)
        print(f"🔐 Signed Upload URL Response: {signed_upload_url}")
        
        # Extract the token
        signed_token = signed_upload_url.get("token")
        if not signed_token:
            raise ValueError("Failed to retrieve the token from the signed upload URL response.")
        
        print(f"🔐 Signed Token: {signed_token}")

        # Write the SRT content to a temporary file
        with open(temp_file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(srt_content)

        # Open the temporary file in binary mode and upload it to Supabase
        with open(temp_file_path, "rb") as file:
            response = supabase.storage.from_(bucket_name).upload_to_signed_url(
                path=srt_filename,
                file=file,
                token=signed_token
            )
        print(f"🔐 Upload Response: {response}")
        # Check the response status
        if response:
            print("✅ SRT file successfully uploaded to Supabase.")
            return f"{bucket_name}/{srt_filename}"
        else:
            print(f"❌ Failed to upload SRT file to Supabase: {response.json()}")
            return ""
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)