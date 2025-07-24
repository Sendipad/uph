# -----------------------------------------------------------------------------
# Project Name: UPH - Unified Party Hub
# File name: uph/hub/utils/normalizer.py
# Description: Text normalization with pluggable methods and LRU caching
# Author: Abdo Ruzaqi (Sendipad)
# License: GNU GPL v3.0
# -----------------------------------------------------------------------------
# Adjusted version of the normalization module according to the recommendations

import frappe
import re
import unicodedata
import phonenumbers
import json
from functools import lru_cache
from typing import Callable, Dict, Optional, Tuple, Union

# =============================================================================
# CONSTANTS
# =============================================================================

DIACRITIC_REGEX = re.compile(r"[\u0610-\u061A\u064B-\u065F\u06D6-\u06ED]")
DIACRITIC_REGEX_EXCEPT_SHADDA = re.compile(
    r"[\u0610-\u061A\u064B-\u0650\u0652-\u065F\u06D6-\u06ED]"
)
PUNCTUATION_REGEX = re.compile(r"[^\w\s]", re.UNICODE)
WHITESPACE_REGEX = re.compile(r"\s+")
ALLAH_PATTERN = re.compile(r"(اللّ?ه[\u064B-\u065F]*)")
PHONE_NUMBER_REGEX = re.compile(r"^\+?[0-9\s\-\(\)\.]+$")

TRANSLATION_TABLE = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ى": "ي",
        "ة": "ه",
        "ؤ": "و",
        "ئ": "ي",
        "ـ": "",
        "ك": "ک",
        "ي": "ی",
        **{chr(0x660 + i): str(i) for i in range(10)},
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

# =============================================================================
# NORMALIZATION PIPELINE
# =============================================================================


class NormalizationPipeline:
    METHODS: Dict[str, Callable[[str, dict], str]] = {}

    def __init__(self, methods: list, params: Optional[dict] = None):
        self.methods = methods
        self.params = params or {}

    def normalize(self, text: str) -> str:
        if not text:
            return ""
        for method in self.methods:
            if method in self.METHODS:
                try:
                    text = self.METHODS[method](text, self.params)
                except Exception as e:
                    frappe.log_error(
                        f"Normalization failed for method '{method}'",
                        f"Value: {text}\nError: {str(e)}",
                    )
            else:
                frappe.log_error(
                    f"Unknown normalization method: {method}", "Normalizer"
                )
        return text

    @classmethod
    def register_method(cls, name: str):
        def decorator(func):
            cls.METHODS[name] = func
            return func

        return decorator


# =============================================================================
# REGISTERED METHODS
# =============================================================================


@NormalizationPipeline.register_method("unicode_normalize")
def unicode_normalize(text: str, params: dict) -> str:
    return unicodedata.normalize(params.get("form", "NFKD"), text)


@NormalizationPipeline.register_method("remove_diacritics")
def remove_diacritics_step(text: str, params: dict) -> str:
    if params.get("preserve_allah", True):
        text = ALLAH_PATTERN.sub(r"<<ALLAH:\1>>", text)
    pattern = (
        DIACRITIC_REGEX_EXCEPT_SHADDA
        if params.get("preserve_shadda")
        else DIACRITIC_REGEX
    )
    text = pattern.sub("", text)
    if params.get("preserve_allah", True):
        text = text.replace("<<ALLAH:", "").replace(">>", "")
    return text


@NormalizationPipeline.register_method("casefold")
def casefold_text(text: str, params: dict) -> str:
    return text.casefold()


@NormalizationPipeline.register_method("character_translation")
def translate_chars(text: str, params: dict) -> str:
    return text.translate(TRANSLATION_TABLE)


@NormalizationPipeline.register_method("remove_punctuation")
def remove_punct(text: str, params: dict) -> str:
    return PUNCTUATION_REGEX.sub("", text)


@NormalizationPipeline.register_method("normalize_whitespace")
def norm_space(text: str, params: dict) -> str:
    return WHITESPACE_REGEX.sub(params.get("replace_with", " "), text).strip()


@NormalizationPipeline.register_method("trim_whitespace")
def trim_ws(text: str, params: dict) -> str:
    return text.strip()


@NormalizationPipeline.register_method("phone_format")
def phone_e164(text: str, params: dict) -> str:
    if not PHONE_NUMBER_REGEX.match(text):
        return text
    try:
        country = params.get("country", "SA")
        phone = phonenumbers.parse(text, country)
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return re.sub(r"[^\d]", "", text)


@NormalizationPipeline.register_method("email_normalize")
def email_norm(text: str, params: dict) -> str:
    if "@" not in text:
        return text
    local, domain = text.rsplit("@", 1)
    local = local.split("+")[0].replace(".", "")
    return f"{local.lower()}@{domain.lower()}"


@NormalizationPipeline.register_method("numeric_only")
def just_digits(text: str, params: dict) -> str:
    return re.sub(r"\D", "", text)


@NormalizationPipeline.register_method("alphanumeric_only")
def alnum_only(text: str, params: dict) -> str:
    return re.sub(r"[^\w]", "", text)


@NormalizationPipeline.register_method("address_standardization")
def standardize_addr(text: str, params: dict) -> str:
    replacements = {
        r"\b(st|street)\b": "Street",
        r"\b(ave|avenue)\b": "Avenue",
        r"\b(rd|road)\b": "Road",
        r"\b(blvd|boulevard)\b": "Boulevard",
        r"\b(apt|apartment)\b": "Apt",
        r"\b(fl|floor)\b": "Floor",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


@NormalizationPipeline.register_method("lower")
def lower_case(text: str, params: dict) -> str:
    return text.lower()


# =============================================================================
# MAIN ENTRYPOINT
# =============================================================================


@frappe.whitelist()
def normalizer(
    value: str,
    profile: str = "default",
    params: Optional[Union[str, dict]] = None,
) -> str:
    if not value:
        return ""

    # Parse params first
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            frappe.log_error("Invalid JSON in normalizer params", params)
            params = {}
    else:
        params = params or {}

    # Determine pipeline from DocType if it exists
    if frappe.db.exists("Normalization Profile", profile):
        pipeline, doc_params = get_profile_pipeline_from_doc(profile)
        params.update(doc_params)
    else:
        pipeline = build_normalization_pipeline(profile, params)

    pipeline_str = ",".join(pipeline)
    frozen_params = tuple(sorted(params.items())) if params else ()
    context_hash = hash(("v1.4", tuple(NormalizationPipeline.METHODS.keys())))

    return _cached_normalize(value, pipeline_str, frozen_params, context_hash)


@lru_cache(maxsize=10000)
def _cached_normalize(
    value: str,
    pipeline_str: str,
    frozen_params: Tuple[Tuple[str, Union[str, int, float, bool]]],
    context_hash: int,
) -> str:
    params = dict(frozen_params)
    steps = [step.strip() for step in pipeline_str.split(",")]
    processor = NormalizationPipeline(steps, params)
    return processor.normalize(value)


def get_profile_pipeline_from_doc(profile_name: str) -> Tuple[list, dict]:
    doc = frappe.get_cached_doc("Normalization Profile", profile_name)
    pipeline = [m.strip() for m in doc.pipeline.split(",")]
    params = json.loads(doc.parameters or "{}")
    return pipeline, params


def build_normalization_pipeline(profile: str, params: dict) -> list:
    """
    Build normalization pipeline based on profile and parameters

    Args:
        profile: Predefined profile name or comma-separated method list
        params: Normalization parameters

    Returns:
        List of normalization methods to apply
    """
    # Custom pipeline definition
    if "," in profile:
        return [step.strip() for step in profile.split(",")]

    # Predefined normalization profiles
    predefined_profiles = {
        "default": [
            "trim_whitespace",
            "unicode_normalize",
            "remove_diacritics",
            "casefold",
            "character_translation",
            "normalize_whitespace",
        ],
        "phone": ["trim_whitespace", "phone_format"],
        "email": ["trim_whitespace", "email_normalize"],
        "numeric": ["trim_whitespace", "numeric_only"],
        "alphanumeric": ["trim_whitespace", "alphanumeric_only"],
        "address": ["trim_whitespace", "casefold", "address_standardization"],
        "light": ["trim_whitespace", "casefold"],
        "strict_arabic": [
            "trim_whitespace",
            "unicode_normalize",
            "remove_diacritics",
            "casefold",
            "character_translation",
            "normalize_whitespace",
        ],
        "diacritics_only": ["remove_diacritics"],
        "clean_text": [
            "trim_whitespace",
            "unicode_normalize",
            "remove_diacritics",
            "casefold",
            "character_translation",
            "remove_punctuation",
            "normalize_whitespace",
        ],
    }

    pipeline = predefined_profiles.get(profile, predefined_profiles["default"])

    # Handle remove_punctuation parameter
    if params.get("remove_punctuation") and "remove_punctuation" not in pipeline:
        # Find optimal position to insert punctuation removal
        if "character_translation" in pipeline:
            index = pipeline.index("character_translation") + 1
        elif "casefold" in pipeline:
            index = pipeline.index("casefold") + 1
        else:
            index = len(pipeline) - 1

        pipeline.insert(index, "remove_punctuation")

    return pipeline


# =============================================================================
# LEGACY
# =============================================================================


def remove_diacritics(text: str) -> str:
    return normalizer(text, profile="diacritics_only", params={"preserve_allah": False})


def normalize_arabic(
    text: str, remove_punctuation: bool = True, preserve_allah: bool = True
) -> str:
    params = {"preserve_allah": preserve_allah, "preserve_shadda": False}
    pipeline = [
        "trim_whitespace",
        "unicode_normalize",
        "remove_diacritics",
        "casefold",
        "character_translation",
    ]
    if remove_punctuation:
        pipeline.append("remove_punctuation")
    pipeline.append("normalize_whitespace")
    return normalizer(text, profile=",".join(pipeline), params=params)


# Warm cache
if frappe.local.dev_server or not frappe.local.flags.in_install:
    for value in ["الله", "محمد", "عبد الله", "example@domain.com", "+966501234567"]:
        for method in ["default", "strict_arabic", "email", "phone"]:
            normalizer(value, method)
