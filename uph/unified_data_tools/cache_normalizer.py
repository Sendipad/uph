import frappe
from uph.unified_data_tools.mdm import normalize_text


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
