import frappe
from frappe import _
from frappe.utils import cint
from uph.party.controllers.cache_utils import (
    get_configured_party_types,
    get_pm_doctypes,
)


def refresh_dashboard_stats():
    """
    Calculates dashboard stats and caches them in Redis.
    Runs hourly.
    """
    stats = {}

    # 1. Unlinked Count
    unlinked_count = 0
    party_types = get_configured_party_types() or ["Customer", "Supplier", "Employee"]

    for dt in party_types:
        if frappe.db.exists("DocType", dt):
            # Check if field exists
            if frappe.get_meta(dt).has_field("party_master"):
                # Use SQL for robust NULL/Empty check
                count = frappe.db.sql(
                    f"SELECT COUNT(*) FROM `tab{dt}` WHERE IFNULL(party_master, '') = ''"
                )[0][0]
                unlinked_count += count

    # 2. Transaction Health
    draft_count = 0
    cancelled_count = 0

    # get_pm_doctypes returns list of dicts or list of lists depending on implementation
    # cache_utils says: fields=["parent_doctype", "document_type", "party_fieldname"], as_list=True
    # so it returns list of tuples/lists: [parent_doctype, document_type, party_fieldname]

    tx_doctypes = get_pm_doctypes() or []
    processed_tx_types = set()

    for row in tx_doctypes:
        # row is [parent_doctype, document_type, party_fieldname]
        doctype = row[0]
        if doctype in processed_tx_types:
            continue

        if not frappe.db.exists("DocType", doctype):
            continue

        meta = frappe.get_meta(doctype)
        if not meta.has_field("docstatus") or not meta.has_field("party_master"):
            continue

        # Drafts: docstatus=0 AND party_master is set
        d_count = frappe.db.sql(
            f"""
            SELECT COUNT(*) FROM `tab{doctype}`
            WHERE docstatus=0 AND IFNULL(party_master, '') != ''
        """
        )[0][0]
        draft_count += d_count

        # Cancelled Unamended
        if meta.has_field("amended_from"):
            c_count = frappe.db.sql(
                f"""
                SELECT COUNT(*) FROM `tab{doctype}`
                WHERE docstatus=2
                AND IFNULL(party_master, '') != ''
                AND IFNULL(amended_from, '') = ''
            """
            )[0][0]
            cancelled_count += c_count

        processed_tx_types.add(doctype)

    # 3. Duplicate Count
    duplicate_count = frappe.db.count("Potential Duplicate", {"status": "Detected"})

    # 4. Incomplete Parties (No party_type set)
    incomplete_count = frappe.db.count(
        "Party Master", {"is_group": 0, "party_type": ["is", "not set"]}
    )

    # Update Cache
    frappe.cache.set_value("uph:stats:unlinked_count", unlinked_count)
    frappe.cache.set_value("uph:stats:incomplete_count", incomplete_count)
    frappe.cache.set_value("uph:stats:health_draft", draft_count)
    frappe.cache.set_value("uph:stats:health_cancelled", cancelled_count)
    frappe.cache.set_value("uph:stats:duplicate_count", duplicate_count)
    frappe.cache.set_value("uph:stats:last_updated", frappe.utils.now())


def run_full_duplicate_scan():
    """
    Scans for duplicates and populates Potential Duplicate table.
    Runs daily.
    """
    # Scans for duplicates and populates Potential Duplicate table.
    # Runs daily.
    # We use NormalizationUtils which handles fuzzy matching and fallbacks.

    # Clear old detected records (optional, or we can upsert)
    # For now, let's keep it simple: finding new ones.

    # 1. Get all Party Masters
    parties = frappe.get_all(
        "Party Master",
        fields=["name", "party_name", "normalized_party_name"],
        filters={"is_group": 0, "status": ["!=", "Disabled"]},
    )

    if len(parties) < 2:
        return

    # Ensure normalized names
    from uph.party.controllers.normalization import NormalizationUtils

    for p in parties:
        if not p.normalized_party_name:
            p.normalized_party_name = NormalizationUtils.normalize_party_name(
                p.party_name
            )
            # Persist for future use
            frappe.db.set_value(
                "Party Master",
                p.name,
                "normalized_party_name",
                p.normalized_party_name,
                update_modified=False,
            )

    # Group by prefix (blocking)
    blocks = {}
    for p in parties:
        if not p.normalized_party_name:
            continue
        prefix = p.normalized_party_name[:2]
        if prefix not in blocks:
            blocks[prefix] = []
        blocks[prefix].append(p)

    # Process blocks
    existing_pairs = set()
    # Load existing pairs to avoid re-inserting
    # This might be heavy if table is huge, better to use unique constraints or INSERT IGNORE in logic

    # Process blocks
    existing_pairs = set()

    # Optimization: If total parties are small, do one big block
    if len(parties) < 1000:
        blocks = {"all": parties}

    for prefix, group in blocks.items():
        if len(group) < 2:
            continue

        # Compare within group
        # Create a list of (normalized_name, party_record) to preserve mapping
        group_data = [
            (p.normalized_party_name, p) for p in group if p.normalized_party_name
        ]
        if not group_data:
            continue

        names = [d[0] for d in group_data]

        for i, p1 in enumerate(group):
            p1_name = p1.normalized_party_name
            if not p1_name:
                continue

            matches = NormalizationUtils.fuzzy_extract(
                p1_name, names, scorer="ratio", limit=10
            )

            for match_name, score, idx in matches:
                p2 = group_data[idx][1]

                if p1.name == p2.name or score < 85:
                    continue

                # Sort pair to ensure consistency
                p_a, p_b = sorted([p1.name, p2.name])

                # Check if exists in Potential Duplicate
                # Use DB exists for now (can be optimized with bulk insert later)
                if not frappe.db.exists(
                    "Potential Duplicate", {"party_1": p_a, "party_2": p_b}
                ):
                    # Also check if Duplicate Exclusion exists
                    if frappe.db.exists(
                        "Duplicate Exclusion", {"party_1": p_a, "party_2": p_b}
                    ):
                        continue

                    doc = frappe.get_doc(
                        {
                            "doctype": "Potential Duplicate",
                            "party_1": p_a,
                            "party_2": p_b,
                            "similarity_score": score,
                            "status": "Detected",
                            "blocking_key": prefix,
                        }
                    )
                    doc.insert(ignore_permissions=True)
