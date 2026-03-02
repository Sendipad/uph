import frappe


def execute():
    """
    IDEMPOTENT: Add indexes to party_master and currency fields.
    Safe to run multiple times - checks if index exists before creating.
    """
    logger = frappe.logger("uph.patches")

    indexes_to_add = [
        {
            "table": "tabCustomer",
            "index_name": "idx_party_master_currency",
            "columns": "(party_master, default_currency)",
        },
        {
            "table": "tabSupplier",
            "index_name": "idx_party_master_currency",
            "columns": "(party_master, default_currency)",
        },
        {
            "table": "tabEmployee",
            "index_name": "idx_party_master_currency",
            "columns": "(party_master, salary_currency)",
        },
    ]

    for index_config in indexes_to_add:
        table = index_config["table"]
        index_name = index_config["index_name"]
        columns = index_config["columns"]

        # Check if index already exists
        index_exists = frappe.db.sql(
            """
            SELECT COUNT(*) as count
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            AND table_name = %s
            AND index_name = %s
        """,
            (table, index_name),
            as_dict=True,
        )

        if index_exists and index_exists[0].get("count", 0) > 0:
            logger.info("Index %s already exists on %s, skipping", index_name, table)
            continue

        # Create index
        try:
            frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX {index_name} {columns}")
            logger.info("Created index %s on %s", index_name, table)
        except Exception as e:
            # Log error but don't fail the patch
            frappe.log_error(
                title=f"Failed to create index {index_name} on {table}",
                message=str(e),
            )
            logger.warning("Failed to create index %s on %s: %s", index_name, table, str(e))

    frappe.db.commit()
