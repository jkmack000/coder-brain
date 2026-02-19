# LEARN-012 — AGENTS.md Cross-Tool Portability Standard
<!-- type: LEARN -->
<!-- tags: agents-md,cross-tool,portability,coding-agents,standards -->
<!-- created: 2026-02-19 -->
<!-- source: github.com/agentsmd/agents.md research session -->
<!-- links: SPEC-001, LEARN-002, RULE-002 -->

## Discovery
AGENTS.md is a vendor-neutral open standard (MIT, 17.6k stars) for giving AI coding agents project-specific instructions via a single markdown file. It is adopted by 21 tools (Codex, Cursor, Gemini CLI, Devin, Copilot, Aider, etc.) and 60k+ repos. Claude Code does NOT support it natively yet (issue #6235, 2.7k+ upvotes). Workaround: `@AGENTS.md` import in CLAUDE.md.

## Context
Evaluated whether AGENTS.md adds value to the Coder Brain system. Conclusion: redundant for the brain itself (CLAUDE.md + .claude/rules/ already cover all AGENTS.md functionality and more), but relevant for cross-tool portability on output repos.

## Evidence
- AGENTS.md is static markdown with no schema — headings for build commands, style, testing, security
- Directory-scoped: nearest AGENTS.md to edited file wins (same pattern as .claude/rules/)
- Our brain system is strictly more capable: typed knowledge, fat indexes, session handoffs, search, dedup
- The brain's CLAUDE.md, RULE-001, RULE-002, RULE-003 already encode everything AGENTS.md would contain

## Impact
- **Brain system:** No changes needed. AGENTS.md is a subset of existing capabilities.
- **Output repos:** Trading strategy repos and infrastructure projects produced by the coder-brain could benefit from an AGENTS.md so non-Claude tools can work on them.
- **Future:** If Claude Code adds native AGENTS.md support, extract static portions of CLAUDE.md into AGENTS.md and `@import` it. Estimated effort: 10 minutes.

## Action Taken
None — flagged for future. Only relevant when cross-tool support becomes a requirement or Claude Code adds native support.

## Open Questions
- Should output repos (trading strategy repos) get auto-generated AGENTS.md files?
