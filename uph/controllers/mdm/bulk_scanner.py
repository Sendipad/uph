"""
Bulk Duplicate Scanner for Data Quality

Optimized for scanning large datasets (10K+ documents).
Uses blocking strategy with sorted neighborhood for O(N log N) complexity.
"""

import frappe
from collections import defaultdict
import time


class BulkDuplicateScanner:
    """
    Optimized bulk duplicate detection engine.
    
    Algorithm:
    1. Fetch all docs once (single query)
    2. Create blocks using blocking keys
    3. Within each block, use sorted neighborhood
    4. In-memory comparison (no repeated DB queries)
    
    Complexity: O(N log N) vs naive O(N²)
    For 10,000 docs: ~30 seconds vs ~15 minutes
    """
    
    def __init__(self, policy, rule):
        self.policy = policy
        self.rule = rule
        self.meta = frappe.get_meta(policy.document_type)
    
    def scan(self, filters=None, batch_size=500):
        """
        Scan for duplicates in bulk.
        
        Args:
            filters: Additional filters for documents
            batch_size: Batch size for progress updates
        
        Returns: Dict with duplicates and stats
        """
        start_time = time.perf_counter()
        
        # Step 1: Fetch ALL data once
        all_docs = self._fetch_all_docs(filters)
        fetch_time = (time.perf_counter() - start_time) * 1000
        
        if len(all_docs) < 2:
            return {
                "duplicates": [],
                "stats": {
                    "total_docs": len(all_docs),
                    "fetch_time_ms": round(fetch_time, 2)
                }
            }
        
        # Step 2: Create blocks
        blocking_start = time.perf_counter()
        blocks = self._create_blocks(all_docs)
        blocking_time = (time.perf_counter() - blocking_start) * 1000
        
        # Step 3: Find duplicates within blocks
        comparison_start = time.perf_counter()
        duplicates = self._find_duplicates_in_blocks(blocks, batch_size)
        comparison_time = (time.perf_counter() - comparison_start) * 1000
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        return {
            "duplicates": duplicates,
            "stats": {
                "total_docs": len(all_docs),
                "blocks_created": len(blocks),
                "duplicate_pairs": len(duplicates),
                "fetch_time_ms": round(fetch_time, 2),
                "blocking_time_ms": round(blocking_time, 2),
                "comparison_time_ms": round(comparison_time, 2),
                "total_time_ms": round(total_time, 2)
            }
        }
    
    def _fetch_all_docs(self, filters):
        """Fetch all docs ONCE with only required fields."""
        required_fields = ["name"] + self.rule.get_required_fields()
        
        base_filters = filters or {"docstatus": ["<", 2]}
        
        docs = frappe.get_all(
            self.policy.document_type,
            filters=base_filters,
            fields=required_fields,
            limit=100000
        )
        
        return docs
    
    def _create_blocks(self, docs):
        """
        Create blocking keys to group similar documents.
        
        Returns: Dict[blocking_key] = [doc1, doc2, ...]
        """
        blocks = defaultdict(list)
        
        for doc in docs:
            blocking_keys = self._get_blocking_keys(doc)
            
            # Add doc to all applicable blocks
            for key in blocking_keys:
                blocks[key].append(doc)
        
        # Remove single-doc blocks
        blocks = {k: v for k, v in blocks.items() if len(v) > 1}
        
        return blocks
    
    def _get_blocking_keys(self, doc):
        """Generate blocking keys for a document."""
        keys = []
        
        for condition in self.rule.conditions:
            if "." in condition.field:
                continue
            
            field = condition.field
            value = doc.get(field)
            
            if not value:
                continue
            
            if condition.check_type == "Exact Match":
                keys.append(f"exact:{field}:{value}")
            
            elif condition.check_type == "Fuzzy Match":
                if condition.is_normalized:
                    norm_value = doc.get(f"normalized_{field}")
                else:
                    from uph.controllers.mdm.normalization import normalize_text
                    norm_value = normalize_text(str(value))
                
                if norm_value and len(norm_value) >= 3:
                    prefix = norm_value[:3]
                    keys.append(f"fuzzy:{field}:{prefix}")
            
            elif condition.check_type == "Date Range":
                try:
                    from frappe.utils import getdate
                    date = getdate(value)
                    year_month = f"{date.year}-{date.month:02d}"
                    keys.append(f"date:{field}:{year_month}")
                except:
                    pass
        
        if not keys:
            keys = ["all"]
        
        return keys
    
    def _find_duplicates_in_blocks(self, blocks, batch_size):
        """Find duplicates within each block using sorted neighborhood."""
        all_duplicates = []
        processed_pairs = set()
        
        total_blocks = len(blocks)
        processed_blocks = 0
        
        for block_key, docs in blocks.items():
            # Sort docs for sorted neighborhood optimization
            docs = self._sort_docs_for_comparison(docs)
            
            # Sliding window comparison
            window_size = min(10, len(docs) - 1)
            
            for i in range(len(docs)):
                for j in range(i + 1, min(i + window_size + 1, len(docs))):
                    doc1 = docs[i]
                    doc2 = docs[j]
                    
                    # Create pair key
                    pair_key = tuple(sorted([doc1["name"], doc2["name"]]))
                    
                    if pair_key in processed_pairs:
                        continue
                    
                    processed_pairs.add(pair_key)
                    
                    # Score the pair
                    score = self.rule.evaluate(doc1, doc2)
                    
                    if score >= self.policy.threshold_score:
                        all_duplicates.append({
                            "doc1": doc1["name"],
                            "doc2": doc2["name"],
                            "score": round(score, 2),
                            "block_key": block_key
                        })
            
            # Progress tracking
            processed_blocks += 1
            if processed_blocks % 100 == 0:
                frappe.publish_realtime(
                    "bulk_scan_progress",
                    {
                        "blocks_processed": processed_blocks,
                        "total_blocks": total_blocks,
                        "duplicates_found": len(all_duplicates)
                    },
                    user=frappe.session.user
                )
        
        # Sort by score descending
        all_duplicates.sort(key=lambda x: x["score"], reverse=True)
        
        return all_duplicates
    
    def _sort_docs_for_comparison(self, docs):
        """Sort docs to improve comparison efficiency."""
        sort_field = None
        max_weight = 0
        
        for condition in self.rule.conditions:
            if condition.check_type == "Fuzzy Match" and condition.weight > max_weight:
                if condition.is_normalized:
                    sort_field = f"normalized_{condition.field}"
                else:
                    sort_field = condition.field
                max_weight = condition.weight
        
        if sort_field and all(doc.get(sort_field) for doc in docs):
            return sorted(docs, key=lambda d: str(d.get(sort_field) or ""))
        
        return docs


# API Functions

@frappe.whitelist()
def run_bulk_duplicate_scan(policy_name, filters=None):
    """
    Run optimized bulk duplicate scan.
    
    Complexity: O(N log N) vs O(N²)
    For 10,000 docs: ~30 seconds vs ~15 minutes
    """
    policy = frappe.get_doc("Data Quality Policy", policy_name)
    rule = frappe.get_cached_doc("Data Quality Rule", policy.data_quality_rule)
    
    scanner = BulkDuplicateScanner(policy, rule)
    result = scanner.scan(filters)
    
    # Log the scan
    log_execution(
        policy=policy.name,
        document_type=policy.document_type,
        trigger_type="Bulk Scan",
        execution_mode="Bulk",
        result=result
    )
    
    return result


@frappe.whitelist()
def schedule_bulk_scan(policy_name, filters=None):
    """Enqueue bulk scan as background job."""
    frappe.enqueue(
        run_bulk_duplicate_scan,
        policy_name=policy_name,
        filters=filters,
        queue="long",
        timeout=7200,
        job_name=f"Bulk Duplicate Scan: {policy_name}"
    )
    
    frappe.msgprint(
        f"Bulk duplicate scan started in background for policy: {policy_name}",
        indicator="blue"
    )


def log_execution(policy, document_type, trigger_type, execution_mode, result, doc_name=None, action_taken=None):
    """Helper to log execution results."""
    stats = result.get("stats", {})
    duplicates = result.get("duplicates", []) or result.get("matches", [])
    
    try:
        frappe.get_doc({
            "doctype": "Data Quality Log",
            "execution_timestamp": frappe.utils.now(),
            "policy": policy,
            "document_type": document_type,
            "document_name": doc_name,
            "trigger_type": trigger_type,
            "execution_mode": execution_mode,
            "total_matches": len(duplicates),
            "highest_score": max([d.get("score", 0) for d in duplicates]) if duplicates else 0,
            "matches_found": frappe.as_json(duplicates),
            "action_taken": action_taken,
            "execution_time_ms": stats.get("total_time_ms", 0),
            "query_time_ms": stats.get("query_time_ms", 0),
            "scoring_time_ms": stats.get("scoring_time_ms", 0),
            "candidates_checked": stats.get("candidates", 0) or stats.get("total_docs", 0),
            "status": "Completed"
        }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to log execution: {str(e)}", "Data Quality Log")
