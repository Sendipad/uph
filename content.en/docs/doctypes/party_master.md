---
title: "Party Master"
weight: 10
description: "No description provided."
---

# Party Master

**Module:** Party

## Overview
No description provided.

## Fields
| Label | Fieldname | Type | Mandatory |
|-------|-----------|------|-----------|
|  | section_break_4hqz | Section Break | No |
| Left | lft | Int | No |
| Right | rgt | Int | No |
| Is Group | is_group | Check | No |
| Old Parent | old_parent | Link | No |
| Parent Party Master | parent_party_master | Link | No |
| Party Type | party_type | Link | No |
| Party Name | party_name | Data | Yes |
| Party Number | party_number | Data | No |
| Group Type | group_type | Link | No |
| Party Type Group | party_type_group | Dynamic Link | No |
|  | column_break_sqyz | Column Break | No |
| Has Secondary Role Party | has_secondary_role_party | Check | No |
| Is Internal Party | is_internal_party | Check | No |
| Represents Company | represents_company | Link | No |
| Territory | territory | Link | No |
| Allowed To Transact With | companies | Table | No |
| Default Currency | default_currency | Link | No |
| Default Price List | default_price_list | Link | No |
| Print Language | language | Link | No |
|  | column_break_14 | Column Break | No |
| Address HTML | address_html | HTML | No |
| Default Payment Terms Template | payment_terms | Link | No |
| Market Segment | market_segment | Link | No |
| Industry | industry | Link | No |
| Primary Party Master | primary_party_master | Link | No |
| More Details | section_break_mnpu | Section Break | No |
| Defaults | section_break_ulyl | Section Break | No |
| Contacts Information | contacts_information_tab | Tab Break | No |
| Contact HTML | contact_html | HTML | No |
| Primary Address and Contact | primary_address_and_contact_detail | Section Break | No |
| Party Primary Contact | party_primary_contact | Link | No |
| Mobile No | mobile_no | Read Only | No |
| Email Id | email_id | Read Only | No |
|  | column_break_26 | Column Break | No |
| Party Primary Address | party_primary_address | Link | No |
| Primary Address | primary_address | Text | No |
| Title | title | Data | No |
|  | column_break_mzed | Column Break | No |
| Is Primary Role | is_primary_role | Check | No |
| Accounting | tab_3_tab | Tab Break | No |
| Type | type | Select | No |
|  | column_break_hllf | Column Break | No |
| Image | image | Attach Image | No |
| Party Details | party_details | Text | No |
| Series | naming_series | Select | No |
|  | section_break_eydo | Section Break | No |
| Total Linked Party | total_linked_party | Int | No |
| Tax | tax_tab | Tab Break | No |
| Tax ID | tax_id | Data | No |
|  | column_break_jsug | Column Break | No |
| Tax Category | tax_category | Link | No |
| Tax Withholding Category | tax_withholding_category | Link | No |
| Portal Users | portal_users_tab | Tab Break | No |
| Party Portal Users | portal_users | Table | No |
| Settings | settings_tab | Tab Break | No |
|  Is Frozen | is_frozen | Check | No |
| Disabled | disabled | Check | No |
|  | column_break_slaa | Column Break | No |
|  | section_break_zygi | Section Break | No |
| Account Group | accounts | Table | No |
| Status | status | Select | No |
|  | section_break_nrbo | Section Break | No |
| Disputed Reasons | disputed_reasons | Text | No |
| Gender | gender | Link | No |
| Salutation | salutation | Link | No |
| Details | details_tab | Tab Break | No |
| Credit Limits | credit_limits | Table | No |
| Party Type Roles | roles | Table MultiSelect | No |
|  | column_break_ihcs | Column Break | No |
| Enable Selling | enable_selling | Check | No |
| Enable Buying | enable_buying | Check | No |
|  | section_break_wnss | Section Break | No |
| Enforce Party Analaytic Accounting Selection | enforce_party_analaytic_accounting_selection | Check | No |
| Dashboard | dashboard_tab | Tab Break | No |
| Relationships | relationships_html | HTML | No |
| Legal Identity | section_break_legal_identity | Section Break | No |
| National ID | national_id | Data | No |
| Passport Number | passport_number | Data | No |
| Business Registration Number | business_registration_number | Data | No |
|  | column_break_legal_identity | Column Break | No |
| Legal Entity Type | legal_entity_type | Select | No |
| Date | date_of_establishment | Date | No |
| Account Manager | account_manager | Link | No |
| Parties | parties | Table | No |
| Normalized Party Name | normalized_party_name | Data | No |

## Permissions
| Role | Read | Write | Create | Delete | Submit | Cancel | Amend |
|------|------|-------|--------|--------|--------|--------|-------|
| System Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
| Accounts Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
| Sales Master Manager | ✓ | ✓ | ✓ |  |  |  |  |
| Purchase Master Manager | ✓ | ✓ | ✓ |  |  |  |  |
| Party Manager | ✓ | ✓ | ✓ | ✓ |  |  |  |
