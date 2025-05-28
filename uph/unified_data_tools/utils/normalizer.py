import frappe
import re
import unicodedata

# from rapidfuzz import fuzz

# Translation table for Arabic, Persian, and Latin accented characters
TRANSLATION_TABLE = str.maketrans(
    {
        # Arabic normalization
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ى": "ي",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ي",
        "ـ": "",  # Tatweel
        # Persian character mapping
        "ك": "ک",
        "ي": "ی",
        # Digit from Indian To Arabic
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
        # Latin accents (lowercase)
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "á": "a",
        "à": "a",
        "â": "a",
        "ä": "a",
        "í": "i",
        "ì": "i",
        "î": "i",
        "ï": "i",
        "ó": "o",
        "ò": "o",
        "ô": "o",
        "ö": "o",
        "ú": "u",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
        "ñ": "n",
        # Latin accents (uppercase)
        "É": "E",
        "È": "E",
        "Ê": "E",
        "Ë": "E",
        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ä": "A",
        "Í": "I",
        "Ì": "I",
        "Î": "I",
        "Ï": "I",
        "Ó": "O",
        "Ò": "O",
        "Ô": "O",
        "Ö": "O",
        "Ú": "U",
        "Ù": "U",
        "Û": "U",
        "Ü": "U",
        "Ç": "C",
        "Ñ": "N",
    }
)

# Arabic diacritic removal regex
DIACRITIC_REGEX = re.compile(r"[\u064B-\u065F]")


@frappe.whitelist()
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = DIACRITIC_REGEX.sub("", text)
    text = text.translate(TRANSLATION_TABLE)
    return text.strip()


def remove_diacritics(text):
    text = unicodedata.normalize("NFKD", text)
    return re.sub(r"[\u064B-\u065F]", "", text)
