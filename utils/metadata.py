import time
import requests
import logging
from config import OPENAI_API_KEY

# Setup logger
logger = logging.getLogger("clip_generator")
logger.setLevel(logging.INFO)

def log_to_dashboard(transcript, result, status, retries):
    """
    Optional: send metadata to your dashboard or internal DB.
    """
    dashboard_payload = {
        "transcript_snippet": transcript[:200],
        "title": result.get("title"),
        "hashtags": result.get("hashtags"),
        "status": status,
        "retries": retries,
        "timestamp": time.time(),
    }
    # Example: POST to your internal analytics or DB endpoint
    # requests.post("http://your-dashboard/api/logs", json=dashboard_payload)
    logger.info(f"Logged clip metadata: {dashboard_payload}")

def generate_clip_metadata(transcript_text, max_retries=3):
    prompt = (
        "You're a creative content editor. Based on this transcript, "
        "generate a viral short-form video TITLE (under 12 words) and 3 relevant HASHTAGS:\n\n"
        f"{transcript_text[:1000]}"
    )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 100
    }

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt+1}: Sending prompt to OpenAI")

            res = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
            res.raise_for_status()

            response_json = res.json()
            content = response_json["choices"][0]["message"]["content"].strip()

            # Parse out title and hashtags from the response
            lines = content.split("\n")
            title = ""
            hashtags = []

            for line in lines:
                if not title and line.strip():
                    title = line.strip()
                elif "#" in line:
                    hashtags.extend(part.strip() for part in line.split() if part.startswith("#"))

            metadata = {"title": title, "hashtags": hashtags[:3]}
            log_to_dashboard(transcript_text, metadata, "success", attempt)
            return metadata

        except requests.exceptions.RequestException as e:
            if res.status_code == 429:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limit hit. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            logger.error(f"HTTP error from OpenAI: {e}")
            log_to_dashboard(transcript_text, {}, "http_error", attempt)
            raise RuntimeError(f"Error communicating with OpenAI API: {e}")

        except Exception as ex:
            logger.error(f"Unexpected error: {ex}")
            log_to_dashboard(transcript_text, {}, "exception", attempt)
            raise RuntimeError(f"Unexpected error: {ex}")

    log_to_dashboard(transcript_text, {}, "failed_max_retries", max_retries)
    raise RuntimeError("Exceeded maximum retries due to rate limits or other errors.")
