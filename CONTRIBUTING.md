Contributing to UPH

Thank you for your interest in contributing to UPH (Unified Party Hub). We welcome contributions that improve stability, usability, documentation, and architecture.

UPH is designed to enhance ERPNext’s party architecture while maintaining compatibility with Frappe standards.


---

📌 Project Scope

UPH focuses on:

Unified Party architecture

Multi-currency support improvements

Party role abstraction (Customer / Supplier / Future roles)

ERPNext compatibility

Clean migration paths

Edge cases in multi-economy environments



---

🧭 Before You Start

1. Search existing issues before opening a new one.


2. If proposing a major architectural change, open a discussion first.


3. Keep contributions aligned with:

Frappe Framework standards

ERPNext design philosophy

Backward compatibility





---

🛠 Development Setup

1️⃣ Prerequisites

Python 3.10+

Node 18+

Bench CLI

ERPNext installed


2️⃣ Clone Repository

cd frappe-bench/apps
git clone https://github.com/Sendipad/uph.git

3️⃣ Install App

bench --site your-site-name install-app uph

4️⃣ Run in Development Mode

bench start


---

🌱 Branching Strategy

main → Stable branch

develop → Active development

Feature branches → feature/<short-description>

Fix branches → fix/<short-description>


Example:

git checkout -b feature/unified-party-migration


---

🧪 Code Standards

Follow Frappe conventions.

Python

Follow PEP8

Use meaningful function names

Avoid breaking API contracts

Keep migration patches safe and idempotent


JavaScript

Use Frappe client scripting standards

Avoid global overrides unless necessary

Keep UI modifications minimal and extensible


DocTypes

Do not remove fields without migration path

Always provide patch scripts for structural changes

Maintain database backward compatibility



---

🧾 Migration Rules

If your contribution:

Renames a field

Alters schema

Moves data

Changes architecture


You must:

1. Add a patch in:

uph/patches/


2. Register it in:

patches.txt


3. Ensure:

No data loss

Safe re-run capability

Works on production databases





---

🐛 Reporting Bugs

When reporting issues, include:

ERPNext version

Frappe version

UPH version

Reproduction steps

Expected behavior

Actual behavior

Screenshots (if UI related)


Use GitHub Issues.


---

🚀 Pull Request Guidelines

Before submitting a PR:

Rebase on latest develop

Ensure no unrelated changes

Provide a clear description

Link related issue

Add migration notes if needed


PR title format:

[TYPE] Short Description

Types:

FEATURE

FIX

REFACTOR

DOCS

PATCH


Example:

[FEATURE] Make party_master optional in report


---

🔒 Stability Policy

UPH prioritizes:

1. Data safety


2. Backward compatibility


3. Production reliability


4. Gradual architectural improvement



Breaking changes require:

Clear migration path

Documentation

Major version bump



---

📖 Documentation Contributions

Improvements to:

Architecture explanation

Multi-currency case documentation

Unified Party philosophy

Installation guides


Are encouraged.


---

🤝 Code of Conduct

Be respectful

Keep discussions technical

Focus on solutions

Avoid personal criticism



---

🧠 Architectural Philosophy

UPH follows:

Canonical Party Identity

Role Extension Model

Ledger integrity preservation

Multi-currency realism


Contributions should align with this long-term vision.


---

📜 License

By contributing, you agree that your contributions will be licensed under the project’s existing license.
