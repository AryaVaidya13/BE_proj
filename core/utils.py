import re

def sanitize_filename(name):
    """Sanitize topic name for safe file saving."""
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

import time
from google.api_core.exceptions import ResourceExhausted


def safe_generate(model, prompt):
    """
    Handles Gemini rate limits automatically.
    Retries after waiting if quota exceeded.
    """
    while True:
        try:
            return model.generate_content(prompt)

        except ResourceExhausted as e:
            print("⚠️ Rate limit hit. Waiting before retry...")

            # Extract retry delay if available
            match = re.search(r"retry_delay {\s*seconds: (\d+)", str(e))
            wait_time = int(match.group(1)) if match else 60

            print(f"⏳ Waiting {wait_time} seconds...")
            time.sleep(wait_time + 2)