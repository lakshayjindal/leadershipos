# File System

## Purpose

This document defines how Leadership OS interacts with the local file system.

Leadership OS is a Local-First application.

All application data is stored on the user's computer.

No cloud storage, synchronization, or external services are required for normal operation.

The file system should remain organized, predictable, and recoverable.

---

# Design Principles

The file system should satisfy the following principles.

- Human Readable
- Predictable
- Portable
- Recoverable
- Minimal
- Self-Contained

Users should always know where their information is stored.

No important data should be hidden in obscure directories without reason.

---

# Storage Categories

Leadership OS stores information in two categories.

1. Operational Data
2. Knowledge Data

---

# Operational Data

Operational data represents the information required for Leadership OS to function.

Examples include:

- Tasks
- Current Day
- Timers
- Application State
- Settings

Operational data is managed entirely by Leadership OS.

Users are generally not expected to edit these files manually.

---

# Knowledge Data

Knowledge data represents permanent information created by the application.

Examples include:

- Daily Journals
- Historical Notes

Knowledge files are intended to be owned by the user.

They should remain editable using any Markdown editor.

Leadership OS should never require proprietary formats.

---

# Default Directory Structure

The application maintains two independent storage locations.

Application Data

```
~/.local/share/leadership-os/
```

Knowledge Base

```
~/Documents/Obsidian/
```

These locations are independently configurable where appropriate.

---

# Application Data

The application data directory contains internal information.

Example structure

```
~/.local/share/leadership-os/

├── database.db
├── config.json
├── state.json
├── logs/
├── backups/
└── cache/
```

This directory is owned by Leadership OS.

---

# Database

Purpose

Persistent operational storage.

Contains

- Tasks
- Sessions
- Daily Records
- Configuration
- Statistics
- Metadata

The database should never contain generated Markdown journals.

---

# Configuration

Example

```
config.json
```

Stores

- User Preferences
- Working Hours
- Theme
- Overlay Settings
- Notification Preferences
- Vault Location

Configuration should remain independent of operational data.

---

# Application State

Example

```
state.json
```

Contains temporary information.

Examples

- Current State
- Active Task
- Running Timer
- Current Day

This file allows Leadership OS to recover gracefully after unexpected shutdown.

---

# Cache

The cache directory stores temporary information.

Examples

- Generated previews
- Temporary exports
- Performance cache

Cache may be safely deleted at any time.

Leadership OS should recreate it automatically.

---

# Logs

Logs exist solely for troubleshooting.

Logs should never contain sensitive user information unless Developer Mode is enabled.

Old log files should be rotated automatically.

---

# Backups

Leadership OS may periodically create backups of operational data.

Backups should include:

- Database
- Configuration
- State

Generated Markdown journals are excluded because they already exist independently.

---

# Obsidian Integration

Leadership OS integrates with an existing Obsidian vault.

Example

```
~/Documents/Obsidian/
```

The vault remains entirely owned by the user.

Leadership OS writes journals only to the configured destination.

The application should never modify unrelated notes.

---

# Daily Notes

Default location

```
~/Documents/Obsidian/Daily Notes/
```

Generated files

```
2026-07-09.md

2026-07-10.md

2026-07-11.md
```

Only one journal may exist for each day.

---

# File Ownership

Leadership OS distinguishes between two ownership models.

Application-Owned

Examples

- Database
- Configuration
- Cache
- Logs
- State

These files should only be modified by Leadership OS.

---

User-Owned

Examples

- Markdown Journals

Users may edit these files freely.

Leadership OS should avoid overwriting manual changes.

---

# File Naming

Generated files should use deterministic names.

Examples

Daily Journal

```
YYYY-MM-DD.md
```

Backups

```
backup-YYYY-MM-DD-HH-MM.db
```

Logs

```
leadership-os.log
```

Predictable naming simplifies searching and recovery.

---

# Recovery

If application data becomes corrupted:

Leadership OS should attempt recovery in the following order.

1. Current Database

2. Latest Backup

3. Rebuild Missing State

Knowledge files should never be affected by operational recovery.

---

# Import

Leadership OS may import:

Configuration

Database

Backup

Importing should never overwrite journals.

---

# Export

Supported exports

Configuration

Database Backup

Entire Workspace

Markdown Journals

Users should always be able to migrate their data.

---

# Data Retention

Leadership OS never automatically deletes:

Tasks

Sessions

Journals

Reflections

Historical records

Temporary files such as logs and cache may be cleaned automatically.

---

# Security

All data remains local.

Leadership OS should never transmit files externally without explicit user action.

No telemetry should access user journals.

No analytics should inspect private notes.

User data belongs entirely to the user.

---

# Portability

A complete Leadership OS workspace should be portable.

Copying:

Database

Configuration

Markdown Journals

should allow complete restoration on another machine.

No internet connection should be required.

---

# Future Expansion

Future versions may introduce:

Encrypted backups

Plugin storage

Attachment storage

Workspace snapshots

Versioned journals

These additions should preserve compatibility with the existing file structure.

---

# Final Principle

The file system is the foundation of Leadership OS.

Operational data enables the application to function.

Markdown journals preserve the user's knowledge.

The application should manage its own internal files while treating user-owned journals as permanent, editable documents that remain accessible regardless of the future of Leadership OS itself.