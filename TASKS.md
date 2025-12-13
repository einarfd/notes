# Development Tasks

## Phase 1: Core Foundation

- [x] Verify project setup works (`uv sync`, imports, basic tests)
- [x] Implement basic Note model with frontmatter parsing
- [x] Implement filesystem storage backend
- [x] Add basic Tantivy search integration
- [x] Wire up MCP tools (create, read, update, delete, list)
- [x] Test MCP server manually with Claude Desktop or similar

## Phase 2: Search & Discovery

- [x] Improve search with better ranking (field boosting, raw tokenizer for tags)
- [x] Add tag-based filtering
- [x] Implement path-based navigation (list notes in folder)
- [x] Add search by date range (with date math: now-7d, 2024-01-01+1M)
- [x] Support markdown links between notes

## Phase 3: AI Optimization

- [ ] Add context tools (get related notes, recent notes)
- [ ] Implement semantic search (embeddings)
- [ ] Add note summarization support
- [ ] Create "knowledge graph" view of note connections

## Phase 4: Multi-client Support

- [x] Test with Claude Desktop
- [ ] Test with other MCP clients
- [x] Document setup for different AI tools
- [x] Add web UI for note management (replaces CLI task)

## Phase 5: Production Hardening

- [x] Add input validation (path traversal prevention, model validators)
- [ ] Add comprehensive error handling for edge cases
- [ ] Implement logging
- [ ] Add user configuration file support
- [x] Write user documentation (README with MCP client setup)
- [x] Add backup/export functionality (CLI and Web UI)

## Backlog / Ideas

- [ ] Team/shared notes support
- [ ] Note versioning/history
- [ ] Encryption for sensitive notes
- [x] Web UI for browsing (moved to Phase 4, completed)
- [ ] Import from other note tools (Obsidian, Notion, etc.)
- [ ] Claude skills integration
