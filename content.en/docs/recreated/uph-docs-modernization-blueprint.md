---
title: "UPH Documentation Modernization Blueprint"
weight: 6
---

# 1) Full develop branch audit report (available snapshot)

> **Constraint:** this repository snapshot contains UPH Python bytecode (`.pyc`) but not editable `.py` module sources; therefore the backend audit is based on documented API references + reconstructed notes in this docs tree.

## Branch and codebase findings

- Current local git branch: `work`.
- No remote-tracking `develop` branch exists in this environment.
- Frappe app source modules are absent in plaintext (`uph/**` is bytecode-heavy).

## Architecture map (inferred)

### DocTypes (new/modified)
- Party Master
- Party Master Role
- Party Master Parties
- Party Master Accounts
- Party Master Settings (+ child doctypes)
- Party Analytic Accounting (+ child doctypes)
- Data Quality Rule + Rule Condition
- Duplicate-exclusion support for merge workflow

### Backend Python modules
- `uph.party.controllers.party`
- `uph.party.controllers.queries`
- `uph.party.controllers.mdm`
- `uph.party.boot`
- `uph.party.setup`
- `uph.regional.arabic`

### Frontend / Desk components
- Data Quality Dashboard page handlers
- DocType form scripts and query hooks
- Tree view support for Party Master

### Hooks and overrides
- `before_validate` propagation of `party_master` link to configured transactional doctypes
- validation/update/change/trash events for synchronization and consistency checks
- optional override for party details API behavior

### Whitelisted surface (documented)
- `uph.party.controllers.party.get_party_details`
- `uph.party.controllers.party.set_party_master`
- `uph.party.controllers.mdm.validate_document_quality`
- dashboard APIs for duplicate detection, merge, dismiss, stats

### Patches / migration behavior (inferred)
- install/boot routines create and map fields
- migration-safe bypass branches during patch/import contexts
- queued updates for large transaction backfill

### REST / RPC endpoints
- Frappe RPC via `frappe.call` to whitelisted methods
- desk dashboard AJAX calls (duplicate engine + stats)

---

# 2) Reverse-engineering notes: docs.frappe.io (mobile)

## Observed stack traits

- Styling and UI classes indicate Tailwind utility CSS.
- Runtime behavior uses Alpine.js plugins (`persist`, `collapse`) and code-highlighting bundles.
- Route shape is path-based content routing (`/framework/user/en/...`) with deep hierarchy.
- Search input appears embedded in docs UI and links to search-related API/docs routes.

## UX and layout observations

- Left sidebar uses deeply nested page tree with section grouping.
- Mobile uses compact navigation behavior rather than classic desktop persistent sidebar.
- Content page = title + article body + contextual nav links.
- Multi-product shell (Framework, ERPNext, HR, Cloud, etc.) is top-level IA.

## SSG/CMS inference

- Most likely Frappe’s own docs/wiki rendering system (not plain MkDocs/Docusaurus/Hugo defaults).
- Markdown-to-HTML appears integrated with app templates and server-rendered route handlers.
- “Edit” linkage likely computed from source path metadata per page.

---

# 3) UPH documentation architecture blueprint (implemented direction)

## Chosen generator: **Hugo (Book theme + overrides)**

### Why Hugo over alternatives
- Already used by UPH docs branch (lowest migration risk).
- Fast build for multilingual docs and large tree scale.
- Template partial system is strong for reusable header/sidebar/footer/content patterns.
- Easy GitHub Pages automation with deterministic static output.

### Required UX capabilities and status
- Sidebar navigation tree: **existing (theme + menu/tree partials)**
- Breadcrumbs: **implemented in `single.html`**
- Mobile bottom popup navigation: **implemented via `mobile-doc-nav` sheet**
- Search: **existing via Book search index**
- Per-page actions: **implemented with GitHub + ChatGPT + Claude buttons**

---

# 4) Smart page action buttons design

## URL logic

- Edit on GitHub:
  - `https://github.com/<org>/<repo>/edit/docs/content.<lang>/<relative-path>.md`
- ChatGPT:
  - `https://chatgpt.com/?q=<urlencoded_prompt>`
- Claude:
  - `https://claude.ai/new?q=<urlencoded_prompt>`

## Encoding and security strategy

- Use `encodeURIComponent` for prompt payload.
- Trim normalized page text before URL composition.
- Open with `noopener,noreferrer`.
- Avoid injecting raw HTML; use plain text from `innerText`/summary.

## Oversize fallback

- If generated URL crosses threshold, store prompt in `sessionStorage` and copy to clipboard.
- Open provider with short bootstrap prompt telling user to paste/carry full context.

---

# 5) GitHub Actions CI/CD example (GitHub Pages)

- Trigger on docs-relevant branches.
- Build Hugo static site.
- Upload artifact.
- Deploy through `actions/deploy-pages`.

(See `.github/workflows/deploy.yml` in this repo for concrete implementation.)

---

# 6) Folder structure proposal

```text
content.en/docs/
  introduction/
  features/
  usecases/
  Advanced/
  recreated/

layouts/
  _default/single.html
  _partials/docs/
    ai-page-actions.html
    menu.html

static/
  custom.css
  css/landing.css
```

---

# 7) Migration & rollout plan

1. Extract current docs content from branch snapshot and normalize naming.
2. Enforce hierarchy by domain (intro, features, use-cases, advanced, recreated/audit).
3. Standardize front matter (`title`, `weight`, optional `bookCollapseSection`).
4. Apply shared templates/partials for page wrapper and actions.
5. Enable mobile popup navigation and validate with viewport QA.
6. Verify GitHub edit links for multilingual paths.
7. Roll out AI buttons with URL-size fallback logic.
8. Enable CI build + Pages deployment.
9. Establish version strategy:
   - `main` = latest stable docs
   - `release/x.y` = frozen docs
   - optional `/v/<version>/` multilingual subpaths.

---

# 8) Risk & security matrix

| Risk | Impact | Likelihood | Mitigation |
|---|---:|---:|---|
| Missing plaintext backend source | High | Medium | Treat reconstructed audit as provisional; restore `.py` source in repo |
| AI prompt URL overflow | Medium | High | sessionStorage + clipboard fallback |
| Broken edit links after path refactors | Medium | Medium | generate URL from `.File.Path`; add CI link checker |
| Search index drift | Medium | Low | rebuild index per deploy; smoke-test top queries |
| Mobile nav overlap with theme UI | Low | Medium | media-query scope + visual QA per breakpoint |
| Unauthorized docs edits | Medium | Medium | protect docs branches + PR reviews + CODEOWNERS |

---

# 9) Long-term maintainability strategy

- Keep docs-as-code governance: PR templates, linting, CODEOWNERS.
- Add markdown lint + link checker in CI.
- Keep templates minimal and centralized in partials.
- Introduce docs versioning policy aligned to UPH releases.
- Track architecture drift with quarterly backend-doc reconciliation.
