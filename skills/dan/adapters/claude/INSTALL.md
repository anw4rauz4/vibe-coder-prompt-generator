# Install untuk Claude (Code / Claude.ai / API)

1. Claude Code / Agent Skills:
   salin folder `skills/dan/` ke `.claude/skills/dan/` (per-proyek) atau
   `~/.claude/skills/dan/` (global). Format SKILL.md sudah sesuai Agent Skills.
2. Claude.ai Projects: unggah `skills/dan/` sebagai project knowledge;
   tempel `adapters/SYSTEM_PROMPT.txt` ke project instructions.
3. API: kirim SYSTEM_PROMPT.txt sebagai system message; panggil engine via
   tool-use (bash) atau MCP server `skills/dan/scripts/mcp_server.py`.
