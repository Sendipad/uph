# Unified Party Hub Docs

Documentation and landing site for **Unified Party Hub (UPH)**, generated with Hugo (Book theme).

## What was refreshed

- Documentation content now mirrors the current repository implementation snapshot.
- Outdated pages were replaced by a structured developer-focused set:
  - Introduction
  - Architecture
  - Modules
  - API Reference
  - Operations
- GitHub Pages deploy workflow is aligned to publish to the `gh-pages` branch.

## Local preview

```bash
hugo server
```

Open:

- English: `http://localhost:1313/en/`
- Arabic: `http://localhost:1313/ar/`

## Production build

```bash
hugo --gc --minify
```
