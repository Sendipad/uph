import frappe
from uph.party.utils import normalize_text


def execute():
    """
    IDEMPOTENT: Populate normalized_party_name for Party Master records.
    Safe to run multiple times - only updates records with empty normalized_party_name.
    """
    frappe.reload_doc("party", "doctype", "party_master")

    # Only fetch records where normalized_party_name is empty or null
    # This makes the patch incremental and safe to re-run
    parties = frappe.db.sql(
        """
        SELECT name, party_name
        FROM `tabParty Master`
        WHERE party_name IS NOT NULL
        AND (normalized_party_name IS NULL OR normalized_party_name = '')
    """,
        as_dict=True,
    )

    if not parties:
        print("✓ All Party Master records already have normalized_party_name populated")
        return

    count = 0
    total = len(parties)

    print(f"Updating normalized_party_name for {total} Party Master records...")

    for idx, party in enumerate(parties, 1):
        try:
            normalized_name = normalize_text(party.party_name)
            frappe.db.set_value(
                "Party Master",
                party.name,
                "normalized_party_name",
                normalized_name,
                update_modified=False,
            )
            count += 1

            # Show progress every 100 records
            if idx % 100 == 0:
                print(f"  Progress: {idx}/{total} records processed...")
                frappe.db.commit()  # Commit in batches

        except Exception as e:
            frappe.log_error(
                title=f"Normalization failed for Party Master {party.name}",
                message=str(e),
            )
            print(f"  ⚠ Failed to normalize {party.name}: {str(e)}")

    frappe.db.commit()
    print(f"✓ Updated normalized_party_name for {count}/{total} Party Master records")
