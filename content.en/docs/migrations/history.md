---
title: "Migrations & History"
weight: 10
---

# Migrations & Patches

UPH follows a strict versioning and migration strategy to ensure production safety.

## Version 3.1.6
- **Refined Group Sync**: Fixed issues with target group existence validation.
- **Standardized Naming**: Enforced 2-letter capitalized prefix/suffix rule.
- **Performance**: Optimized tree balance queries using Redis caching.

## Migration Flow
- **After Migrate Hook**: `uph.setup.install.on_migrate` handles schema updates and index verification.
- **Fixtures**: Core workflows and roles are managed via fixtures for deployment stability.
