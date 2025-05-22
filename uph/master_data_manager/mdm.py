# Copyright (c) 2024, Abdo Ruzaqi and contributors
# For license information, please see license.txt
"""
A module that control Data Quality and deduplications , It hold many usuful utility functions

"""

import frappe

import re
import unicodedata
from rapidfuzz import fuzz


class RedisNormalizerCache:
    def __init__(self, doctype, default_ttl=86400, field_ttls=None):
        self.doctype = doctype
        self.default_ttl = default_ttl
        self.field_ttls = field_ttls or {}
        self.redis = frappe.cache()

    def _key(self, field):
        return f"normalized:{self.doctype}:{field}"

    def _get_ttl(self, field):
        return self.field_ttls.get(field, self.default_ttl)

    def get(self, field, raw_value):
        return self.redis.hget(self._key(field), raw_value)

    def set(self, field, raw_value, normalized_value):
        key = self._key(field)
        self.redis.hset(key, raw_value, normalized_value)
        self.redis.expire(key, self._get_ttl(field))

    def normalize(self, field, value):
        if not value:
            return ""
        cached = self.get(field, value)
        if cached:
            return cached
        normalized = normalize_text(value)
        self.set(field, value, normalized)
        return normalized

    def normalize_bulk(self, field, values):
        return {v: self.normalize(field, v) for v in values}

    def clear(self, field=None):
        if field:
            self.redis.delete_value(self._key(field))
        else:
            # Clear common fields if needed
            for f in ["first_name", "last_name", "phone", "email_id"]:
                self.redis.delete_value(self._key(f))


class BaseDeduplicationManager:
    def __init__(self, doctype, fields, mode="Fuzzy", weights=None, threshold=85):
        self.doctype = doctype
        self.fields = fields
        self.mode = mode  # "Fuzzy" or "Exact"
        self.weights = weights or {f: 1 for f in fields}
        self.threshold = threshold
        self.conditions = {}

        if self.mode == "Fuzzy":
            self.normalizer = RedisNormalizerCache(doctype)

    def configure_conditions(self, filters=None):
        self.conditions = filters or {}

    def get_records(self):
        fields = ["name"] + self.fields
        return frappe.get_all(self.doctype, fields=fields, filters=self.conditions)

    def normalize_record(self, record):
        return {f: self.normalizer.normalize(f, record.get(f)) for f in self.fields} | {
            "name": record["name"]
        }

    def score_similarity(self, a, b):
        score = 0
        total = sum(self.weights.values())
        for field in self.fields:
            score += self.weights[field] * fuzz.ratio(
                a.get(field, ""), b.get(field, "")
            )
        return score / total if total else 0

    def find_duplicates(self):
        records = self.get_records()
        if self.mode == "Fuzzy":
            records = [self.normalize_record(r) for r in records]

        seen = {}
        duplicates = []

        for i, a in enumerate(records):
            key = tuple(a[f] for f in self.fields)

            if self.mode == "Exact":
                if key in seen:
                    duplicates.append(
                        {"original": seen[key], "duplicate": a["name"], "fields": key}
                    )
                else:
                    seen[key] = a["name"]

            elif self.mode == "Fuzzy":
                for b in records[i + 1 :]:
                    score = self.score_similarity(a, b)
                    if score >= self.threshold:
                        duplicates.append(
                            {
                                "original": a["name"],
                                "duplicate": b["name"],
                                "score": round(score, 2),
                            }
                        )

        return duplicates


class RemarkEngine:
    def __init__(self, doc):
        self.doc = doc
        self.context = {"doc": self.doc.as_dict()}

    def generate(self):
        rulesets = frappe.get_all(
            "Custom Remark Rule",
            filters={
                "document_type": self.doc.doctype,
                "enabled": 1,
            },
            order_by="priority desc",
            fields=["name"],
        )

        for ruleset in rulesets:
            rule_doc = frappe.get_doc("Custom Remark Rule", ruleset.name)

            # Skip rules with no template
            if not rule_doc.template or not rule_doc.template.strip():
                continue

            if self.evaluate_filters(rule_doc.conditions):
                try:
                    remark = frappe.render_template(
                        rule_doc.template, self.context
                    ).strip()
                    if remark:  # only accept if rendering produces something
                        return remark
                except Exception as e:
                    frappe.log_error(f"Error rendering template: {e}", "Remark Engine")
                    continue  # continue to next rule if render failed

        return ""

    def evaluate_filters(self, conditions):
        context = self.doc.as_dict()
        for f in conditions:
            field_val = context.get(f.field) or ""
            compare_val = f.value

            try:
                if f.condition == "==":
                    if not str(field_val) == compare_val:
                        return False
                elif f.condition == "!=":
                    if not str(field_val) != compare_val:
                        return False
                elif f.condition == ">":
                    if not float(field_val) > float(compare_val):
                        return False
                elif f.condition == "<":
                    if not float(field_val) < float(compare_val):
                        return False
                elif f.condition == ">=":
                    if not float(field_val) >= float(compare_val):
                        return False
                elif f.condition == "<=":
                    if not float(field_val) <= float(compare_val):
                        return False
            except Exception as e:
                frappe.log_error(f"Error in condition evaluation: {e}", "Remark Engine")
                return False

        return True


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
