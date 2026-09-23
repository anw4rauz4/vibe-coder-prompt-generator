# PLUG-AND-PLAY — memasang DAN di AI mana pun

Paket DAN dirancang agar **satu sumber kebenaran** bisa dipakai di banyak runtime:
persona & routing ada di `skills/dan/AGENT.md` + `skills/dan/SKILL.md`;
`make_adapters.py` mengekspornya ke format tiap platform sehingga **tidak ada drift**.

```bash
cd skills/dan/scripts
python3 make_adapters.py            # ekspor semua adapter -> adapters/
python3 make_adapters.py validate   # cek artefak (0 masalah = siap pasang)
python3 make_adapters.py --only cursor,gemini
```

---

## Matriks runtime

| Runtime | Artefak | Cara pasang | Tool/eksekusi |
|---|---|---|---|
| **Claude Code / Agent Skills** | `skills/dan/` (sudah format SKILL.md) | salin ke `.claude/skills/dan/` (proyek) atau `~/.claude/skills/dan/` (global) | bash / MCP |
| **Claude Desktop** | `adapters/SYSTEM_PROMPT.txt` + `skills/dan/references` | Project instructions + knowledge; MCP untuk tool | **MCP** |
| **Claude API** | `SYSTEM_PROMPT.txt` | system message; tool-use → MCP server | **MCP** |
| **Cursor** | `adapters/cursor/rules/*.mdc` | salin ke `.cursor/rules/` di proyek | terminal / MCP |
| **Gemini CLI / Gemini Code Assist** | `adapters/gemini/GEMINI.md` | letakkan `GEMINI.md` di root proyek | shell / MCP |
| **Google Gems** | `adapters/gemini/gems/*.txt` | tempel per-Gem (satu sub-skill per Gem) | — |
| **ChatGPT (Custom GPT)** | `adapters/chatgpt/custom_gpt_instructions.txt` | Instructions + upload `references/`+`templates/` sebagai Knowledge | Action/MCP |
| **GitHub Copilot** | `adapters/copilot/copilot-instructions.md` | salin ke `.github/copilot-instructions.md` | — |
| **Windsurf** | `adapters/windsurf/rules/dan.md` | salin ke `.windsurf/rules/` | terminal / MCP |
| **Zed** | `adapters/zed/settings_snippet.json` + AGENTS.md | context_servers di settings Zed | **MCP** |
| **Continue.dev** | `adapters/continue/config_snippet.json` | gabungkan ke `~/.continue/config.json` | **MCP** |
| **n8n** | `adapters/n8n/dan-weekly-workflow.json` | impor workflow, ganti `<abs>`, cron Senin | Execute Command |
| **Dify / Flowise** | `adapters/dify-flowise/NOTES.md` (tidak digenerate otomatis) | node Tool/HTTP → `dan.pyz`/MCP | **MCP** |
| **Codex/agent lain (AGENTS.md)** | `adapters/agents/AGENTS.md` | salin ke root repo | terminal / MCP |
| **VS Code (lokal)** | `.vscode/` (settings, tasks, launch, mcp, snippets) + `dan.code-workspace` | buka folder repo di VS Code; semua task tersedia via Ctrl+Shift+P → Tasks | terminal + **MCP** (Copilot agent mode) |
| **Runtime apa pun** | `adapters/SYSTEM_PROMPT.txt` | tempel sebagai system prompt | panggil CLI via shell |

> Prinsip: **skill = dokumen (Markdown ber-frontmatter)**, **tool = engine CLI / MCP**.
> Runtime tanpa eksekusi kode tetap memakai seluruh pengetahuan (routing, framework,
> checklist, template); runtime dengan eksekusi mendapat hasil artefak sungguhan.

---

## 1. Claude (Code / Projects / API)

**Agent Skills (paling native):**
```bash
mkdir -p .claude/skills
cp -r skills/dan .claude/skills/dan          # per-proyek
# atau global:
cp -r skills/dan ~/.claude/skills/dan
```
Claude memuat `SKILL.md` (orchestrator) lalu sub-skill/referensi sesuai kebutuhan
(progressive disclosure). Engine dipanggil lewat bash:
`python3 .claude/skills/dan/scripts/dan.py list`.

**Claude Desktop / API:** tempel `adapters/SYSTEM_PROMPT.txt`, unggah
`skills/dan/references/` + `templates/` sebagai knowledge, dan pasang MCP (bagian 5).

---

## 2. Cursor
```bash
mkdir -p .cursor/rules
cp adapters/cursor/rules/*.mdc .cursor/rules/
```
- `dan-core.mdc` = router inti (description-based, aktif saat konteks cocok).
- `dan-01..21.mdc` = satu rule per sub-skill (description memicu konteks).
Cursor juga dapat menjalankan engine di terminal proyek, atau MCP (bagian 5).

---

## 3. Gemini
```bash
cp adapters/gemini/GEMINI.md .        # konteks proyek utk Gemini CLI / Code Assist
```
Untuk **Gems**: buat satu Gem per sub-skill dan tempel isi
`adapters/gemini/gems/NN-*.txt` sebagai instruksinya.

---

## 4. ChatGPT & Copilot
- **Custom GPT**: Instructions ← `adapters/chatgpt/custom_gpt_instructions.txt`
  (sudah dipangkas ≤8000 karakter); Knowledge ← unggah `references/` + `templates/`.
- **Copilot**: salin `adapters/copilot/copilot-instructions.md` ke
  `.github/copilot-instructions.md`.

---

## 5. MCP — satu server untuk SEMUA klien

`skills/dan/scripts/mcp_server.py` adalah server MCP stdio tanpa dependensi.
Contoh konfigurasi klien:

**Claude Desktop** (`claude_desktop_config.json`):
```json
{ "mcpServers": { "dan": {
    "command": "python3",
    "args": ["/abs/path/skills/dan/scripts/mcp_server.py"] } } }
```

**Claude Code**:
```bash
claude mcp add dan -- python3 /abs/path/skills/dan/scripts/mcp_server.py
```

**Cursor** (`.cursor/mcp.json`):
```json
{ "mcpServers": { "dan": {
    "command": "python3",
    "args": ["/abs/path/skills/dan/scripts/mcp_server.py"] } } }
```

**Gemini CLI**:
```bash
gemini mcp add dan python3 /abs/path/skills/dan/scripts/mcp_server.py
```

**Tool yang tersedia (10):**
`dan_list_skills` · `dan_list_engines` · `dan_run_engine(engine,args[])` ·
`dan_demo` · `dan_rag_query` · `dan_lint_prompt` · `dan_project_status` ·
`dan_arch_compute` · `dan_stack_recommend` · `dan_weekly_summary`

Uji cepat handshake:
```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
              '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | python3 skills/dan/scripts/mcp_server.py
```

Keamanan: `dan_run_engine` dibatasi **whitelist** engine DAN; path tetap milik Anda,
server tidak mengakses jaringan.

---

## 5b. VS Code lokal (langkah detail)
1. Buka folder repositori ini di VS Code (`File → Open Folder`).
2. `.vscode/` sudah berisi: `settings.json` (path analisis Python), `tasks.json`
   (DAN: QA penuh / demo / kasus / ritme mingguan / adapter / MCP smoke),
   `launch.json` (debug engine aktif atau `dan.py` dengan argumen), `mcp.json`
   (server MCP DAN untuk Copilot agent mode), dan snippet `danrun`/`danchart`/`danguard`.
3. Opsional multi-root: buka `dan.code-workspace` agar skills/adapters/deliverables/
   data tampil bersamaan.
4. Regenerasi berkas VS Code kapan pun: `python3 make_adapters.py --only vscode`
   (salinan distribusi ada di `adapters/vscode/dot_vscode/` bila folder Anda berbeda).
5. Verifikasi: jalankan task **DAN: QA penuh** → harus SEHAT.

## 6. Mode tanpa runtime AI sama sekali
- Single file: `deliverables/dan.pyz` (zipapp) — `python3 dan.pyz list|run|doctor`.
- Arsip siap-import: `deliverables/dan-skill-<v>.zip` + `manifest.json` (sha256) + `INSTALL.md`.
- QA mandiri: `python3 skills/dan/scripts/_test_all.py` dan `run_cases.py run all`.

---

## 7. Verifikasi setelah pasang
```bash
python3 skills/dan/scripts/make_adapters.py validate   # 0 masalah
python3 skills/dan/scripts/_test_all.py                # 0 gagal
python3 skills/dan/scripts/_check_refs.py              # 0 referensi hilang
python3 skills/dan/scripts/dan.py demo                 # tur 01-21
```

## 8. Menjaga sinkronisasi (anti-drift)
Setelah mengubah `AGENT.md` / menambah sub-skill:
1. `python3 make_adapters.py` (regenerasi semua adapter),
2. `python3 make_adapters.py validate`,
3. `python3 make_package.py --version <v>` (manifest + zip + pyz),
4. catat di `CHANGELOG.md` → `python3 make_digest.py` untuk tim.
