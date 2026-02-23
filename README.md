# Unified Party Hub Docs

This repository currently contains a Hugo docs site and now also includes an alternative MkDocs setup.

## Why pages may not open

If you open generated files directly (double-clicking `index.html`), navigation and assets can fail because this project uses absolute paths and language subdirectories.

For Hugo, always run a local server:

```bash
hugo server
```

Then open `http://localhost:1313/en/`.

## Alternative static site generator (Frappe-like docs style)

A MkDocs Material setup is included in `mkdocs.yml` and `docs/`.

Run it with:

```bash
pip install mkdocs-material
mkdocs serve
```

Then open `http://127.0.0.1:8000`.
