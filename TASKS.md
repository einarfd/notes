# Development Tasks

## Phase 1: Core Foundation

- [x] Verify project setup works (`uv sync`, imports, basic tests)
- [x] Implement basic Note model with frontmatter parsing
- [x] Implement filesystem storage backend
- [x] Add basic Tantivy search integration
- [x] Wire up MCP tools (create, read, update, delete, list)
- [x] Test MCP server manually with Claude Desktop or similar

## Phase 2: Search & Discovery

- [ ] Improve search with better ranking
- [x] Add tag-based filtering
- [ ] Implement path-based navigation (list notes in folder)
- [ ] Add search by date range
- [ ] Support markdown links between notes

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
- [ ] Add backup/export functionality

## Backlog / Ideas

- [ ] Team/shared notes support
- [ ] Note versioning/history
- [ ] Encryption for sensitive notes
- [x] Web UI for browsing (moved to Phase 4, completed)
- [ ] Import from other note tools (Obsidian, Notion, etc.)
- [ ] Claude skills integration
