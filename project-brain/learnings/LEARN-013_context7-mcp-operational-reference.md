# LEARN-013 — Context7 MCP Operational Reference
<!-- type: LEARN -->
<!-- tags: context7,mcp,documentation,api-reference,claude-code,upstash -->
<!-- created: 2026-02-19 -->
<!-- source: github.com/upstash/context7 research session -->
<!-- links: SPEC-001, LEARN-002, LEARN-011 -->

## Discovery
Context7 is an MCP server (MIT, 46k stars, by Upstash) that injects up-to-date, version-specific library documentation into LLM prompts. It is the brain's tier-2 knowledge source (brain files > Context7 > GitHub). The MCP server is a thin client; parsing/indexing/reranking happens server-side (closed source).

## Setup for Claude Code

### Remote (recommended — no local deps)
```bash
# With API key (higher rate limits)
claude mcp add --scope user --header "CONTEXT7_API_KEY: YOUR_API_KEY" --transport http context7 https://mcp.context7.com/mcp

# Without API key
claude mcp add --scope user --transport http context7 https://mcp.context7.com/mcp
```

### Local (requires Node.js 18+)
```bash
claude mcp add --scope user context7 -- npx -y @upstash/context7-mcp --api-key YOUR_API_KEY
```

### Quick setup
```bash
npx ctx7 setup --claude
```

### Verify
```bash
claude mcp list
```

### API key
- Free at context7.com/dashboard
- Format: `ctx7sk-**********************`
- Shown only once — store securely

## Tools Exposed

### 1. `resolve-library-id`
Resolves a library name to a Context7 library ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | User's question (for relevance ranking) |
| `libraryName` | string | Yes | Library name to search |

Returns: list of matches with `id` (`/org/project`), `trustScore` (High>=7), `benchmarkScore` (0-100), `totalSnippets`, `versions`.

### 2. `query-docs`
Retrieves documentation and code examples for a library.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `libraryId` | string | Yes | From resolve-library-id (e.g., `/vercel/next.js`) |
| `query` | string | Yes | Specific question |

Returns: plain text docs with code examples.

### Shortcuts
- **Skip resolution:** Include library ID directly: `use context7 with /ccxt/ccxt`
- **Pin version:** `/vercel/next.js/v14.3.0-canary.87`

### Hard limit: max 3 calls per tool per question.

## Trading Stack Library IDs (to verify at runtime)
- CCXT: likely `/ccxt/ccxt`
- Freqtrade: likely `/freqtrade/freqtrade`
- pandas: likely `/pandas-dev/pandas`
- numpy: likely `/numpy/numpy`
- ta-lib: may not be indexed (Python wrapper)
- VectorBT: search `vectorbt`
- Optuna: search `optuna`
- pytest: search `pytest`

**Not all libraries are indexed.** Submit missing ones at context7.com/add-library.

## Gotchas

1. **Rate limits** — Without API key: very low, daily reset. With free key: higher. Returns HTTP 429 when exceeded.
2. **Query quality matters** — "How to set up JWT auth middleware in Express.js" >> "auth". Be specific.
3. **Windows timeout errors** — Common; may need full Node.js path instead of `npx`. Use remote server to avoid.
4. **Node.js 18+ required** for local server.
5. **Thin client** — Cannot self-host the full system, only the MCP server client.
6. **Privacy** — Only MCP-formulated queries sent to Context7 (not full prompts/code). Queries pass through third-party LLMs for reranking. Queries stored server-side for benchmarking (Enterprise can disable).
7. **No freshness SLA** — Docs are crawled periodically. Library owners can manually trigger refresh. The "10-15 days" estimate in SPEC-001 is approximate, not guaranteed.
8. **Library state** — Some libraries return 202 (still processing) or 422 (too large/no code).
9. **Trust scores** — Check `trustScore` and `benchmarkScore` before relying on unfamiliar library docs.

## Best Practices

1. Get an API key (even free tier helps)
2. Be specific with queries
3. Use library IDs directly when known (saves a tool call)
4. Pin versions for version-specific docs
5. Add auto-invocation rule to CLAUDE.md: "Always use Context7 MCP when I need library/API documentation"
6. Use remote server to avoid Node.js platform issues
7. Cache responses when working on the same library repeatedly

## Context7 Plugin (optional)
Beyond the basic MCP server, a plugin adds:
- **Skills:** Auto-triggers doc lookups (no "use context7" needed)
- **Agents:** `docs-researcher` agent runs on Sonnet in separate context
- **Commands:** `/context7:docs <library> [query]`

Install: `/plugin marketplace add upstash/context7`

## Open Questions
- Which trading stack libraries are actually indexed in Context7? Need runtime verification.
- Is the Context7 plugin stable enough for production use?
