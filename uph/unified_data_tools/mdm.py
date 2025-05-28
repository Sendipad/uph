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
