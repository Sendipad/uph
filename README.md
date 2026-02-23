# Unified Party Hub Docs

This repository uses Hugo (Book theme). A MkDocs scaffold also exists, but Hugo is the primary production generator.

## Why pages may not open

If you open generated files directly (double-clicking `index.html`), navigation and assets can fail because this project uses absolute paths and language subdirectories.

Use a server instead.

## See generated pages **without merge**

You have two good options:

### 1) Local preview from your branch

```bash
hugo server
```

Then open:

- English: `http://localhost:1313/en/`
- Arabic: `http://localhost:1313/ar/`

### 2) PR preview artifact in GitHub Actions

For every PR to `main`, workflow **Docs Preview (PR)** builds Hugo and uploads artifact `hugo-preview-site`.

Steps:

1. Open your PR checks.
2. Open workflow **Docs Preview (PR)**.
3. Download artifact `hugo-preview-site`.
4. Run a static server from extracted folder:

```bash
python3 -m http.server 8000 --directory public
```

Then open `http://localhost:8000/en/`.

---

## Alternative static site generator (Frappe-like docs style)

A MkDocs Material setup is included in `mkdocs.yml` and `docs/`.

```bash
pip install mkdocs-material
mkdocs serve
```

Then open `http://127.0.0.1:8000`.
