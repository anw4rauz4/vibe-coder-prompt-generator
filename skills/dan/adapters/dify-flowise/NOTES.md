# Dify / Flowise

DSL keduanya proprietary & berubah cepat, jadi TIDAK kami generate otomatis.
Cara integrasi yang stabil:
1. Buat node *Tool/HTTP* yang memanggil `dan.pyz`/`mcp_server.py` (mis. `python3 dan.pyz run dan_analytics data.csv`).
2. Atau ekspos MCP server paket ini dan daftarkan sebagai plugin MCP di Dify.
3. Tempel `SYSTEM_PROMPT.txt` ke LLM node sebagai system message.
