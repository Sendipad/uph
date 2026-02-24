---
title: "API Reference"
weight: 5
---

# API Reference (from bytecode symbols)

> Endpoint availability below reflects discovered whitelisted/search/report functions in compiled modules.

## Hook-registered integrations

- `boot_session`: `uph.party.boot.add_pm_doctypes`
- `after_install`: `uph.setup.install.setup`
- Global doc events:
  - `uph.party.controllers.party.validate_party_master_on_target_party_type`
  - `uph.party.controllers.party.validate_party_master_on_document_types`

## Query / link search endpoints

From `uph.party.controllers.queries`:

- `party_master_link_query(doctype, txt, searchfield, page_len, start, filters, reference_doctype)`
- `get_party_master(doctype, txt, searchfield, start, page_len, filters)`
- `get_unlinked_party(filters, limit)`
- `get_linked_parties_list(party_master_filters, party_type)`
- `query_similar_name_or_number(party_name, party_number)`
- `get_counts_of_unposted_or_cancelled_vouchers(company, party_master, is_party_gl_effected)`
- `make_warning_for_not_submitted_voucher(party_master, as_count)`

## Party Master endpoints

From `uph.party.doctype.party_master.party_master`:

- `get_party_master_balances(company)`
- `get_parents(doctype, child)`
- `get_children(doctype, parent, company, name, is_root)`
- `get_next_party_master_number(parent, is_group)`
- `create_party_from_party_master(source_name, target_doctype, save, target_doc, rule_field_value)`
- `get_unset_parties_list(doctype, txt, searchfield, start, page_len, filters, as_dict)`
- `get_parties(party_master, fromdb, party_type)`
- `create_party_master(doc)`
- `check_similar_party_name(party_name, doctype, start, page_len)`
- `assign_party_master_for_selections_list(assign_parties)`
- `assign_party_master_for_selection(old_party_master, new_party_master, selections)`
- `make_contact(args, is_primary_contact)`
- `make_address(args, is_primary_address, is_shipping_address)`
- `map_party_to_target(source_name, target_doctype, save, rule_field_value, target_doc)`

## Utility endpoints

- `uph.party.utils.get_party_master_list(...)` (search helper)
- `uph.party.controllers.field.get_field_options(doctype)`
- `uph.party.report.party_master_health_report.get_party_type_summary(filters)`

## Script reports (`execute(filters)`)

- `party_account_statement`
- `party_account_balances`
- `chronological_party_ledger`
- `party_master_health_report`
