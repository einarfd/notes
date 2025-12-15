# Wiki-AI Data Model

This document defines the core data structures used in wiki-ai.

## Note

A note is the fundamental unit of content.

### Schema

```yaml
Note:
  path: string          # Unique identifier, e.g., "projects/wiki-ai/ideas"
  title: string         # Human-readable display name
  content: string       # Markdown content
  tags: string[]        # Optional tags for categorization
  created_at: string    # ISO8601 timestamp
  updated_at: string    # ISO8601 timestamp
```

### Example

```yaml
path: "projects/wiki-ai/ideas"
title: "Product Ideas"
content: |
  # Product Ideas

  Initial brainstorm for wiki-ai features:
  - Multi-LLM support via MCP
  - Human-readable storage format
  - Full-text search with BM25
tags:
  - brainstorm
  - product
created_at: "2024-01-15T10:30:00Z"
updated_at: "2024-01-15T14:22:00Z"
```

---

## Path Conventions

Paths are hierarchical, similar to file system paths but without a leading slash.

### Rules

1. **No leading slash**: `projects/wiki-ai`, not `/projects/wiki-ai`
2. **No trailing slash**: `projects/wiki-ai`, not `projects/wiki-ai/`
3. **Allowed characters**: alphanumeric, hyphens, underscores
4. **Case sensitive**: `Projects/Idea` and `projects/idea` are different
5. **Depth**: No hard limit, but recommend max 5 levels
6. **Uniqueness**: Paths must be unique across all notes

### Valid Examples

```
ideas
projects/wiki-ai
projects/wiki-ai/research/mcp
meetings/2024/01/standup-15
```

### Invalid Examples

```
/projects/wiki-ai     # Leading slash
projects/wiki-ai/     # Trailing slash
projects//wiki-ai     # Double slash
projects/wiki ai      # Space in path
```

### Folders and Hierarchy

Folders are implicit - they exist when notes have paths under them. There's no separate folder entity.

**A path can be both a note AND have child notes.** This allows for wiki-like "index" or "overview" notes:

```
projects/wiki-ai          ← a note (project overview)
projects/wiki-ai/ideas    ← child note
projects/wiki-ai/research ← child note
```

This is valid and encouraged. The note at `projects/wiki-ai` can serve as an overview or index for the notes beneath it.

Example: If these notes exist:
- `projects/wiki-ai` (overview note)
- `projects/wiki-ai/ideas`
- `projects/wiki-ai/research`
- `projects/other/notes`

Then these implicit folders exist:
- `projects/` (contains note `wiki-ai` + folder `wiki-ai/` + folder `other/`)
- `projects/wiki-ai/` (contains notes `ideas`, `research`)
- `projects/other/` (contains note `notes`)

When browsing, notes at a path are shown separately from child notes under that path.

---

## Tags

Tags are simple strings for categorization.

### Rules

1. **Lowercase**: Tags are stored lowercase
2. **No spaces**: Use hyphens for multi-word tags (`in-progress`, not `in progress`)
3. **Allowed characters**: alphanumeric and hyphens
4. **No duplicates**: A note can't have the same tag twice

### Examples

```yaml
tags:
  - brainstorm
  - high-priority
  - mcp
  - v1
```

---

## Content Format

Note content is Markdown.

### Recommendations

- Use standard Markdown (CommonMark)
- Headers, lists, code blocks, links all supported
- No embedded images initially (future consideration)
- Keep content focused - split large topics into multiple notes

### Example Content

```markdown
# MCP Protocol Research

## Overview

The Model Context Protocol (MCP) provides a standardized way for AI assistants
to access external tools and data.

## Key Concepts

- **Tools**: Functions the AI can call
- **Resources**: Data the AI can read
- **Prompts**: Templates for common interactions

## Links

- [MCP Documentation](https://modelcontextprotocol.io)
- Related: [[projects/wiki-ai/ideas]]
```

---

## Wiki Links

Notes can link to other notes using wiki-style double bracket syntax.

### Syntax

```markdown
[[path/to/note]]              # Link by path
[[path/to/note|Display Text]] # Link with custom display text
```

### Examples

```markdown
See [[projects/wiki-ai/ideas]] for the full list.

This relates to the [[research/mcp|MCP research]] we did earlier.

Related notes:
- [[meetings/2024-01-15]]
- [[projects/wiki-ai/spec]]
```

### Broken Links

Links to non-existent notes are allowed ("red links"). This enables:
- Drafting content before creating all linked notes
- Creating placeholder links for future content
- Wikipedia-style workflows

To find broken links, use `get_backlinks` on paths that don't exist - it will return any notes linking to that non-existent path.

### Behavior on Move

When a note is moved (path changed via `update_note`):
- Links TO the moved note may become broken
- Use `update_backlinks: true` to automatically update all notes that link to the old path
- Without this flag, a warning lists affected notes but doesn't modify them

### Behavior on Delete

When a note is deleted:
- Links TO the deleted note become broken
- A warning lists affected notes but they are NOT modified
- Automatic link removal is not supported (would mangle surrounding text)
- User must manually update or remove broken links if desired

### Backlinks

The system tracks which notes link to which other notes. This enables:
- `get_backlinks(path)` - find all notes linking to a given note
- Warning about affected notes on move/delete
- "What links here" functionality

---

## Timestamps

All timestamps use ISO8601 format in UTC.

### Format

```
YYYY-MM-DDTHH:MM:SSZ
```

### Examples

```
2024-01-15T10:30:00Z
2024-12-07T14:22:33Z
```

### Behavior

- `created_at`: Set when note is created, never changes
- `updated_at`: Updated whenever note content, title, or tags change
- Moving a note (changing path) updates `updated_at`

---

## Storage Considerations

This specification doesn't mandate storage format, but suggests:

### Option 1: Markdown Files with Frontmatter

Store each note as a `.md` file with YAML frontmatter:

```markdown
---
title: Product Ideas
tags: [brainstorm, product]
created_at: 2024-01-15T10:30:00Z
updated_at: 2024-01-15T14:22:00Z
---

# Product Ideas

Initial brainstorm for wiki-ai features...
```

File path mirrors note path: `projects/wiki-ai/ideas.md`

### Option 2: Database + Object Storage

- Metadata in SQLite/Postgres
- Content in S3-compatible storage
- Better for search indexing and scale

### Option 3: Single SQLite Database

- All data in one file
- Simple deployment
- Good for personal use

---

## Version History

Notes supports git-based version history for tracking all changes to notes. Every create, update, and delete operation is recorded as a git commit.

### Storage

Version history is stored in a git repository within the notes directory. Each note operation creates an atomic commit with:
- The changed file(s)
- A descriptive commit message (e.g., "Create note: path", "Update note: path")
- Author information
- Timestamp

### NoteVersion Schema

```yaml
NoteVersion:
  commit_sha: string    # Git commit SHA (full 40 characters)
  timestamp: string     # ISO8601 timestamp of the commit
  author: string        # Author name from the commit
  message: string       # Commit message
```

### Example

```yaml
commit_sha: "abc1234567890abcdef1234567890abcdef123456"
timestamp: "2024-01-15T14:30:00Z"
author: "alice"
message: "Update note: projects/wiki-ai/ideas"
```

### NoteDiff Schema

```yaml
NoteDiff:
  path: string          # Path of the note
  from_version: string  # Starting commit SHA
  to_version: string    # Ending commit SHA
  diff_text: string     # Unified diff output
  additions: number     # Number of lines added
  deletions: number     # Number of lines deleted
```

### Example

```yaml
path: "projects/wiki-ai/ideas"
from_version: "abc1234"
to_version: "def5678"
diff_text: |
  --- a/projects/wiki-ai/ideas.md
  +++ b/projects/wiki-ai/ideas.md
  @@ -10,7 +10,9 @@
   Initial brainstorm:
  -- Basic search
  +- Full-text search
  +- Version history
additions: 2
deletions: 1
```

### Author Tracking

- **MCP (stdio mode)**: Author is provided via the mandatory `--author` flag when starting the server
- **Web UI**: Author is the authenticated username, or "web" if authentication is disabled

### Restore Behavior

Restoring a note to a previous version does NOT rewrite git history. Instead, it:
1. Reads the content from the specified version
2. Creates a new commit with that content
3. All previous versions remain accessible

This ensures version history is always preserved and can be audited.
