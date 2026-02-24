---
title: "Documentation"
weight: 1
bookCollapseSection: false
---

# UPH Technical Documentation

This documentation is generated from the **current branch implementation**. Because this repository snapshot contains compiled Python bytecode (`.pyc`) instead of source `.py`, module behavior is documented from bytecode inspection (`marshal` + Python code object metadata), hooks values, and module symbols.

## Scope

- Frappe app hooks and lifecycle integration.
- Party Master domain models and DocType controllers.
- Whitelisted API endpoints and report executors.
- Cache logic, query helpers, validation rules, and background/update routines.
- GitHub Pages docs deployment.

## Sections

- [Introduction](/uph/en/docs/introduction/)
- [Architecture](/uph/en/docs/architecture/)
- [Modules](/uph/en/docs/modules/)
- [API Reference](/uph/en/docs/api/)
- [Operations](/uph/en/docs/operations/)
