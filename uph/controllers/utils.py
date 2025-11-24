import frappe
from frappe.model import no_value_fields
import re
import unicodedata
from functools import lru_cache

# Constants for normalization
DIACRITIC_REGEX = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED]")
WHITESPACE_REGEX = re.compile(r"\s+")

TRANSLATION_TABLE = str.maketrans({
    # Arabic normalization
    "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ـ": "",
    # Persian character mapping
    "ك": "ک", "ي": "ی",
    # Digits from Indian to Arabic
    **{chr(0x660 + i): str(i) for i in range(10)},
    # Latin accents (lowercase)
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "á": "a", "à": "a", "â": "a", "ä": "a",
    "í": "i", "ì": "i", "î": "i", "ï": "i",
    "ó": "o", "ò": "o", "ô": "o", "ö": "o",
    "ú": "u", "ù": "u", "û": "u", "ü": "u",
    "ç": "c", "ñ": "n",
    # Latin accents (uppercase)
    "É": "E", "È": "E", "Ê": "E", "Ë": "E",
    "Á": "A", "À": "A", "Â": "A", "Ä": "A",
    "Í": "I", "Ì": "I", "Î": "I", "Ï": "I",
    "Ó": "O", "Ò": "O", "Ô": "O", "Ö": "O",
    "Ú": "U", "Ù": "U", "Û": "U", "Ü": "U",
    "Ç": "C", "Ñ": "N",
})


@frappe.whitelist()
def normalize_text(text: str) -> str:
    """Wrapper for _normalize_text_cached to be used in API calls."""
    return _normalize_text_cached(text)


@lru_cache(maxsize=1024)
def _normalize_text_cached(text: str) -> str:
    """
    Normalize text for fuzzy matching.
    Applies: trim, unicode normalization (NFKD), remove diacritics, casefold, 
    character translation, and whitespace normalization.
    """
    if not text:
        return ""
    
    # 1. Trim whitespace
    text = text.strip()
    
    # 2. Unicode Normalize (NFKD decomposes characters)
    text = unicodedata.normalize("NFKD", text)
    
    # 3. Remove Diacritics (All combining marks + Arabic diacritics)
    # We use category 'Mn' (Mark, Nonspacing) to catch all combining marks
    text = "".join(c for c in text if not unicodedata.category(c).startswith("M"))
    
    # Also apply Arabic specific regex if needed (though Mn might cover it, let's be safe)
    text = DIACRITIC_REGEX.sub("", text)
    
    # 4. Casefold (lower case + aggressive normalization)
    text = text.casefold()
    
    # 5. Character Translation (unify chars)
    text = text.translate(TRANSLATION_TABLE)
    
    # 6. Normalize Whitespace (collapse multiple spaces)
    text = WHITESPACE_REGEX.sub(" ", text).strip()
    
    return text


# Cache field options for 1 hour
@frappe.whitelist()
def get_field_options(doctype):
    cache_key = f"field_options:{doctype}"
    cached = frappe.cache().get_value(cache_key)

    if cached:
        return cached

    result = _get_field_options(doctype)
    frappe.cache().set_value(cache_key, result, expires_in_sec=3600)
    return result


def _get_field_options(doctype):
    """Return all available fields including child tables"""
    meta = frappe.get_meta(doctype)
    options = []

    # Parent fields
    for field in meta.fields:
        if field.fieldtype not in no_value_fields:
            options.append(
                {
                    "label": f"{field.label} ({field.fieldname})",
                    "value": field.fieldname,
                    "fieldtype": field.fieldtype,
                    "options": field.options,
                }
            )

    # Child table fields
    for table_field in meta.get_table_fields():
        child_meta = frappe.get_meta(table_field.options)
        for child_field in child_meta.fields:
            if child_field.fieldtype not in no_value_fields:
                options.append(
                    {
                        "label": f"{table_field.label} → {child_field.label}",
                        "value": f"{table_field.fieldname}.{child_field.fieldname}",
                        "fieldtype": child_field.fieldtype,
                        "options": child_field.options,
                    }
                )

    return options
