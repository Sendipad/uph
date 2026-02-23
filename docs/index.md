# Unified Party Hub

A unified documentation experience for UPH with a layout similar to modern Frappe-style docs.

## Why this version opens reliably

If your current site did not open, common reasons are:

1. The Hugo site expects `/en/` and `/ar/` language subpaths.
2. Opening generated files directly from disk breaks absolute links.
3. Running without a local server means theme assets may not load.

This MkDocs setup runs with a simple local server and avoids those issues.

## Run locally

```bash
pip install mkdocs-material
mkdocs serve
```

Open `http://127.0.0.1:8000`.

## What you get

- Left navigation and sticky table of contents.
- Search, fast page transitions, and copy buttons.
- Styling close to Frappe documentation patterns.
