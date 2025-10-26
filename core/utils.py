import re

def sanitize_filename(name):
    """Sanitize topic name for safe file saving."""
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
