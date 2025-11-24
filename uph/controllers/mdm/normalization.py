import unicodedata
import re
from functools import lru_cache
from uph.controllers.utils import normalize_text as base_normalize

# Re-export base normalization for convenience
normalize_text = base_normalize

@lru_cache(maxsize=1024)
def normalize_for_blocking(text):
    """
    Aggressive normalization for blocking keys.
    Removes all non-alphanumeric characters.
    """
    if not text:
        return ""
    
    # Use base normalization first
    text = base_normalize(text)
    
    # Keep only alphanumeric
    return "".join(c for c in text if c.isalnum())
