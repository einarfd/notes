# Wiki-AI MCP Tools Specification

This document defines the MCP tools exposed by a wiki-ai server.

## Overview

| Tool | Purpose |
|------|---------|
| `create_note` | Create a new note |
| `get_note` | Retrieve a note by path |
| `update_note` | Modify a note (content, title, tags, or path) |
| `delete_note` | Remove a note |
| `search_notes` | Full-text search with query syntax |
| `browse` | List notes and subfolders at a path |
| `list_tags` | Get all tags in use |
| `get_backlinks` | Find notes that link to a given note |
| `recent_notes` | List recently updated notes |
| `get_note_history` | Get version history for a note |
| `get_note_version` | Read a specific version of a note |
| `diff_note_versions` | Compare two versions of a note |
| `restore_note_version` | Restore a note to a previous version |

---

## create_note

Create a new note at the specified path.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path for the note (e.g., `projects/wiki-ai/ideas`). Must be unique. |
| `title` | string | Yes | Human-readable title for the note |
| `content` | string | Yes | Markdown content |
| `tags` | string[] | No | Tags for categorization |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path for the note (e.g., 'projects/wiki-ai/ideas')"
    },
    "title": {
      "type": "string",
      "description": "Human-readable title"
    },
    "content": {
      "type": "string",
      "description": "Markdown content"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Tags for categorization"
    }
  },
  "required": ["path", "title", "content"]
}
```

### Response

Success: Confirmation message with the created note's path and metadata.

```
Created note "My Ideas" at projects/wiki-ai/ideas
```

Error: If path already exists or is invalid.

---

## get_note

Retrieve a note by its path.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path of the note to retrieve |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path of the note"
    }
  },
  "required": ["path"]
}
```

### Response

Success: Full note content with metadata.

```markdown
# My Ideas

**Path:** projects/wiki-ai/ideas
**Tags:** brainstorm, product
**Created:** 2024-01-15T10:30:00Z
**Updated:** 2024-01-15T14:22:00Z

---

Here are my initial ideas for the wiki-ai project...
```

Error: If note not found.

---

## update_note

Update an existing note. All fields except `path` are optional - only provided fields are updated.

To **move** a note, provide `new_path`.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Current path of the note |
| `new_path` | string | No | New path (for moving the note) |
| `title` | string | No | New title |
| `content` | string | No | New content (replaces existing) |
| `tags` | string[] | No | Replace all tags (mutually exclusive with add_tags/remove_tags) |
| `add_tags` | string[] | No | Tags to add (atomic, no race conditions) |
| `remove_tags` | string[] | No | Tags to remove (atomic, no race conditions) |
| `update_backlinks` | boolean | No | When moving, update wiki links in other notes (default: false) |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Current path of the note"
    },
    "new_path": {
      "type": "string",
      "description": "New path (to move the note)"
    },
    "title": {
      "type": "string",
      "description": "New title"
    },
    "content": {
      "type": "string",
      "description": "New content (replaces existing)"
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Replace all tags (mutually exclusive with add_tags/remove_tags)"
    },
    "add_tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Tags to add atomically"
    },
    "remove_tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Tags to remove atomically"
    },
    "update_backlinks": {
      "type": "boolean",
      "description": "When moving, update wiki links in other notes (default: false)"
    }
  },
  "required": ["path"]
}
```

### Tag Operation Behavior

- **`tags`**: Full replacement. Removes all existing tags and sets new ones.
- **`add_tags`**: Adds tags to existing set. Idempotent - adding a tag that exists is a no-op.
- **`remove_tags`**: Removes tags from existing set. Idempotent - removing a tag that doesn't exist is a no-op.
- **`add_tags` + `remove_tags`**: Can be combined. Removals are applied first, then additions.
- **`tags` + `add_tags`/`remove_tags`**: Error. Cannot mix full replacement with incremental operations.

### Response

Success: Confirmation of update.

```
Updated note at projects/wiki-ai/ideas
```

**Moving without `update_backlinks`** (or `update_backlinks: false`):

```
Moved note from projects/wiki-ai/ideas to archive/old-ideas

Warning: 3 notes have links that now point to the old path:
- meetings/2024-01-15 (2 links)
- projects/wiki-ai/overview (1 link)
- research/mcp (1 link)

Use update_backlinks: true to automatically update these links.
```

**Moving with `update_backlinks: true`**:

```
Moved note from projects/wiki-ai/ideas to archive/old-ideas

Updated links in 3 notes:
- meetings/2024-01-15 (2 links)
- projects/wiki-ai/overview (1 link)
- research/mcp (1 link)
```

Error: If note not found or new_path conflicts.

### Future Extension

A separate `edit_note` tool may be added for partial content edits (append, prepend, find/replace) rather than full replacement.

---

## delete_note

Delete a note by path.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path of the note to delete |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path of the note to delete"
    }
  },
  "required": ["path"]
}
```

### Response

Success: Confirmation of deletion.

```
Deleted note at projects/wiki-ai/ideas
```

**When other notes link to the deleted note:**

```
Deleted note at projects/wiki-ai/ideas

Warning: 3 notes have links that are now broken:
- meetings/2024-01-15 (2 links)
- projects/wiki-ai/overview (1 link)
- research/mcp (1 link)

These links were not modified. Update or remove them manually if desired.
```

Note: Unlike move, delete does NOT offer automatic link updates - removing links from content would mangle surrounding text.

Error: If note not found.

---

## search_notes

Full-text search across all notes with pagination.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `query` | string | Yes | Search query with optional field filters |
| `limit` | number | No | Max results to return (default: 10) |
| `cursor` | string | No | Pagination cursor from previous search |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query with optional field filters"
    },
    "limit": {
      "type": "number",
      "description": "Max results (default 10)"
    },
    "cursor": {
      "type": "string",
      "description": "Pagination cursor from previous search"
    }
  },
  "required": ["query"]
}
```

### Query Syntax

The query string supports full-text search with field-specific filters:

| Syntax | Description | Example |
|--------|-------------|---------|
| `word` | Match word in title or content | `mcp` |
| `"phrase"` | Match exact phrase | `"model context protocol"` |
| `title:word` | Match word in title only | `title:meeting` |
| `tag:value` | Filter by tag | `tag:research` |
| `folder:path` | Filter by folder (prefix match) | `folder:projects/wiki-ai` |
| `AND` / `OR` | Boolean operators | `mcp AND tag:research` |
| `-term` | Exclude term | `mcp -tag:archived` |
| `(...)` | Grouping | `(tag:urgent OR tag:priority)` |

**Example queries:**

```
mcp
  → Full-text search for "mcp" in title or content

title:meeting
  → Notes with "meeting" in the title

mcp tag:research
  → Notes containing "mcp" with tag "research"

folder:projects/wiki-ai
  → All notes under projects/wiki-ai/

"model context protocol" tag:mcp -tag:archived
  → Exact phrase, with tag mcp, excluding archived

(tag:urgent OR tag:priority) folder:projects
  → Urgent or priority notes in projects folder
```

Note: Exact query syntax may vary by implementation. The examples above represent recommended baseline support.

### Response

Success: List of matching notes with snippets, total count, and pagination cursor.

```
Found 47 notes (showing 1-10):

- **MCP Integration Ideas** (projects/wiki-ai/mcp-ideas)
  Tags: mcp, integration
  ...discussing **MCP** protocol options for the wiki...

- **Protocol Research** (research/protocols)
  Tags: research
  ...the Model Context Protocol (**MCP**) provides...

- **Meeting Notes Jan 15** (meetings/2024-01-15)
  Tags: meeting
  ...decided to use **MCP** as primary interface...

[... 7 more results ...]

Next page cursor: eyJzY29yZSI6MC43NSwiZG9jIjoxMjN9
```

To get the next page, call `search_notes` with the same query/filters and the cursor:

```json
{
  "query": "mcp",
  "limit": 10,
  "cursor": "eyJzY29yZSI6MC43NSwiZG9jIjoxMjN9"
}
```

No results:

```
No notes found matching "quantum computing"
```

Last page (no more results):

```
Found 47 notes (showing 41-47):

[... results ...]

No more results.
```

### Pagination Behavior

- **Cursor is opaque**: Clients should not parse or construct cursors
- **Cursor encodes position**: Implementation may encode score, doc ID, offset, or other data
- **Same query required**: Cursor is only valid with the same query string
- **Cursor expiry**: Implementations may expire cursors after a reasonable time

---

## browse

List notes and subfolders at a given path. Used for navigating the folder structure.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | No | Folder path to browse (default: root, i.e., empty string) |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Folder path to browse (omit or empty for root)"
    }
  }
}
```

### Response

Success: List of folders and notes at the path.

```
Browsing: projects/

Folders:
- projects/wiki-ai/    (3 notes)
- projects/other/      (1 note)

Notes at this level:
- **Project Index** (projects/index) - Updated 2024-01-15
- **Ideas Backlog** (projects/ideas) - Updated 2024-01-10
```

**When a path is both a note AND has children:**

A path can have a note at it AND child notes underneath. When browsing such a path, show the note separately:

```
Browsing: projects/wiki-ai/

Note at this path:
- **Wiki-AI Overview** (projects/wiki-ai) - Updated 2024-01-20

Folders:
- projects/wiki-ai/research/    (2 notes)

Notes at this level:
- **Product Ideas** (projects/wiki-ai/ideas) - Updated 2024-01-18
- **Technical Spec** (projects/wiki-ai/spec) - Updated 2024-01-15
```

Empty folder:

```
Browsing: archive/

No folders or notes at this path.
```

---

## list_tags

Get all tags currently in use across all notes.

### Arguments

None.

### Input Schema

```json
{
  "type": "object",
  "properties": {}
}
```

### Response

Success: List of tags with usage counts.

```
Tags in use:

- brainstorm (5 notes)
- mcp (3 notes)
- research (3 notes)
- meeting (2 notes)
- product (2 notes)
- priority (1 note)
```

No tags:

```
No tags in use yet.
```

---

## get_backlinks

Get all notes that link to a given note path. Useful for understanding relationships and impact of changes.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path of the note to find backlinks for |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path of the note to find backlinks for"
    }
  },
  "required": ["path"]
}
```

### Response

Success: List of notes that contain links to the specified path.

```
Backlinks to projects/wiki-ai/ideas:

- **Meeting Notes Jan 15** (meetings/2024-01-15)
  2 links - lines 15, 42

- **Wiki-AI Overview** (projects/wiki-ai/overview)
  1 link - line 8

- **MCP Research** (research/mcp)
  1 link - line 23
```

No backlinks:

```
No notes link to projects/wiki-ai/ideas
```

Note not found (still returns backlinks if any exist - useful for finding broken links):

```
Note projects/wiki-ai/ideas does not exist.

However, 2 notes have links to this path:
- meetings/2024-01-15 (2 links)
- projects/wiki-ai/overview (1 link)
```

---

## recent_notes

Get recently created or updated notes. Useful for resuming work and finding recent activity.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | number | No | Max notes to return (default: 10) |
| `since` | string | No | Only notes updated after this ISO8601 timestamp |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "limit": {
      "type": "number",
      "description": "Max notes to return (default 10)"
    },
    "since": {
      "type": "string",
      "description": "Only notes updated after this ISO8601 timestamp"
    }
  }
}
```

### Response

Success: List of recently updated notes, most recent first.

```
Recent notes:

- **MCP Integration Ideas** (projects/wiki-ai/mcp-ideas)
  Updated: 2024-01-15T14:30:00Z
  Tags: mcp, integration

- **Meeting Notes Jan 15** (meetings/2024-01-15)
  Updated: 2024-01-15T11:00:00Z
  Tags: meeting

- **Product Roadmap** (projects/wiki-ai/roadmap)
  Updated: 2024-01-14T16:45:00Z
  Tags: planning, product
```

With `since` filter:

```
Notes updated since 2024-01-15T00:00:00Z:

- **MCP Integration Ideas** (projects/wiki-ai/mcp-ideas)
  Updated: 2024-01-15T14:30:00Z

- **Meeting Notes Jan 15** (meetings/2024-01-15)
  Updated: 2024-01-15T11:00:00Z
```

No recent notes:

```
No notes updated since 2024-01-15T00:00:00Z
```

---

## get_note_history

Get the version history for a note, showing all changes with timestamps and authors.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path of the note |
| `limit` | number | No | Max versions to return (default: 50, max: 100) |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path of the note"
    },
    "limit": {
      "type": "number",
      "description": "Max versions to return (default 50)"
    }
  },
  "required": ["path"]
}
```

### Response

Success: List of versions with commit SHA, timestamp, author, and message.

```
Version history for projects/wiki-ai/ideas:

- abc1234 (2024-01-15T14:30:00Z) by alice
  Update note: projects/wiki-ai/ideas

- def5678 (2024-01-15T10:30:00Z) by bob
  Create note: projects/wiki-ai/ideas
```

No history available:

```
No version history available for projects/wiki-ai/ideas
```

---

## get_note_version

Read a specific historical version of a note.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path of the note |
| `version` | string | Yes | Commit SHA (short or full) |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path of the note"
    },
    "version": {
      "type": "string",
      "description": "Commit SHA (short or full)"
    }
  },
  "required": ["path", "version"]
}
```

### Response

Success: The note content at that version with metadata.

```markdown
# My Ideas (version abc1234)

**Path:** projects/wiki-ai/ideas
**Tags:** brainstorm, product
**Version:** abc1234
**Created:** 2024-01-15T10:30:00Z
**Updated:** 2024-01-15T14:22:00Z

---

Here are my initial ideas for the wiki-ai project...
```

Error: If version not found.

---

## diff_note_versions

Show the differences between two versions of a note.

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path of the note |
| `from_version` | string | Yes | Starting version (older) |
| `to_version` | string | Yes | Ending version (newer) |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path of the note"
    },
    "from_version": {
      "type": "string",
      "description": "Starting version (commit SHA)"
    },
    "to_version": {
      "type": "string",
      "description": "Ending version (commit SHA)"
    }
  },
  "required": ["path", "from_version", "to_version"]
}
```

### Response

Success: Unified diff with change statistics.

```
Diff for projects/wiki-ai/ideas (abc1234 → def5678):

+3 additions, -1 deletions

--- a/projects/wiki-ai/ideas.md
+++ b/projects/wiki-ai/ideas.md
@@ -10,7 +10,9 @@
 Initial brainstorm for wiki-ai features:
 - Multi-LLM support via MCP
 - Human-readable storage format
-- Basic search
+- Full-text search with BM25
+- Tag-based organization
+- Version history
```

---

## restore_note_version

Restore a note to a previous version. This creates a NEW commit with the old content, preserving all history (never rewrites git history).

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | string | Yes | Path of the note |
| `version` | string | Yes | Version SHA to restore |

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Path of the note"
    },
    "version": {
      "type": "string",
      "description": "Version SHA to restore"
    }
  },
  "required": ["path", "version"]
}
```

### Response

Success: Confirmation that the note was restored.

```
Restored note 'projects/wiki-ai/ideas' to version abc1234
```

Error: If note or version not found.
