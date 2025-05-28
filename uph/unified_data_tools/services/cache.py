import frappe

# import hashlib
# from frappe.utils import cint


class RedisCache:
    def __init__(self, doctype):
        self.doctype = doctype
        self.client = frappe.cache
        self.default_ttl = 86400  # 24 hours

    def make_key(self, field):
        return f"dedupe:norm:{self.doctype}:{field}"

    def normalize(self, field, value):
        if not value:
            return ""

        key = self.make_key(field)
        cached = self.client.hget(key, value)

        if cached:
            return cached.decode("utf-8")

        normalized = self._normalize_value(value)
        self.client.hset(key, value, normalized)
        self.client.expire(key, self.default_ttl)
        return normalized

    def normalize_bulk(self, field, values):
        with self.client.pipeline() as pipe:
            for v in values:
                pipe.hget(self.make_key(field), v)
            cached = pipe.execute()

        normalized = []
        for i, v in enumerate(values):
            if cached[i]:
                normalized.append(cached[i].decode("utf-8"))
            else:
                norm_val = self._normalize_value(v)
                normalized.append(norm_val)
                self.client.hset(self.make_key(field), v, norm_val)

        return normalized

    def _normalize_value(self, value):
        """Basic normalization - override for custom logic"""
        if isinstance(value, str):
            return value.lower().strip()
        return str(value)

    def clear(self, field=None):
        if field:
            self.client.delete(self.make_key(field))
        else:
            keys = self.client.keys(f"dedupe:norm:{self.doctype}:*")
            if keys:
                self.client.delete(*keys)
