import frappe
from rapidfuzz import fuzz
from uph.master_data_manager.cache_normalizer import RedisNormalizerCache


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
