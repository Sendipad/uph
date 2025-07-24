# filepath: apps/uph/uph/hub/services/cache.py
import frappe
import json
from datetime import datetime
from frappe.utils import cstr

class RedisCache:
    def __init__(self):
        self.conn = frappe.cache()
    
    def get(self, key):
        value = self.conn.get_value(key)
        if value and isinstance(value, bytes):
            return json.loads(value.decode('utf-8'))
        return value
    
    def set(self, key, value, expiry=None):
        serialized = json.dumps(value, default=self.json_serializer)
        self.conn.set_value(key, serialized, expires_in_sec=expiry)
    
    def delete(self, key):
        self.conn.delete_key(key)
    
    def get_keys(self, pattern):
        return self.conn.get_keys(pattern)
    
    def hget(self, hash, key):
        return self.conn.hget(hash, key)
    
    def hset(self, hash, key, value):
        self.conn.hset(hash, key, value)
    
    def json_serializer(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

# Cache keys
RULE_APPLICABILITY_KEY = "rule_applicability"
RULE_DOC_KEY_PREFIX = "rule_doc:"
CONDITION_TREE_KEY_PREFIX = "condition_tree:"
RULE_LAST_UPDATED_KEY = "rule_last_updated"

cache = RedisCache()

def get_rule_applicability_key(doctype, event, docstatus):
    return f"{RULE_APPLICABILITY_KEY}:{doctype}:{event}:{cstr(docstatus)}"

def get_rule_doc_key(rule_name):
    return f"{RULE_DOC_KEY_PREFIX}{rule_name}"

def get_condition_tree_key(rule_name):
    return f"{CONDITION_TREE_KEY_PREFIX}{rule_name}"

def get_cached_applicable_rules(doctype, event, docstatus):
    key = get_rule_applicability_key(doctype, event, docstatus)
    return cache.get(key)

def set_cached_applicable_rules(doctype, event, docstatus, rules):
    key = get_rule_applicability_key(doctype, event, docstatus)
    cache.set(key, rules, expiry=86400)  # Cache for 24 hours

def get_cached_rule_doc(rule_name):
    key = get_rule_doc_key(rule_name)
    return cache.get(key)

def set_cached_rule_doc(rule_name, rule_doc):
    key = get_rule_doc_key(rule_name)
    cache.set(key, rule_doc, expiry=3600)  # Cache for 1 hour

def get_cached_condition_tree(rule_name):
    key = get_condition_tree_key(rule_name)
    return cache.get(key)

def set_cached_condition_tree(rule_name, condition_tree):
    key = get_condition_tree_key(rule_name)
    cache.set(key, condition_tree, expiry=3600)  # Cache for 1 hour

def get_rule_last_updated():
    return cache.get(RULE_LAST_UPDATED_KEY)

def set_rule_last_updated(timestamp=None):
    if not timestamp:
        timestamp = frappe.utils.now_datetime()
    cache.set(RULE_LAST_UPDATED_KEY, timestamp)

def clear_rule_applicability_cache():
    keys = cache.get_keys(f"{RULE_APPLICABILITY_KEY}:*")
    for key in keys:
        cache.delete(key)

def clear_rule_doc_cache(rule_name=None):
    if rule_name:
        cache.delete(get_rule_doc_key(rule_name))
        cache.delete(get_condition_tree_key(rule_name))
    else:
        keys = cache.get_keys(f"{RULE_DOC_KEY_PREFIX}*") + \
               cache.get_keys(f"{CONDITION_TREE_KEY_PREFIX}*")
        for key in keys:
            cache.delete(key)

def clear_rule_caches(rule_name=None):
    clear_rule_applicability_cache()
    clear_rule_doc_cache(rule_name)
    set_rule_last_updated()
