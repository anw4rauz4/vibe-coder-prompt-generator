# Onboarding Kit — mulai pakai DAN dalam 10 menit

Untuk anggota tim baru (teknis maupun non-teknis). Urutan terbaik:

## 1. Dengarkan & lihat (2 menit)
- **Audio briefing**: `deliverables/onboarding_audio.mp3` (naskah: `onboarding_naskah.txt`).
- **Slide**: buka `deliverables/slides.html` → panah ←/→; Ctrl/Cmd+P untuk PDF.

## 2. Jalankan tur hidup (3 menit)
```bash
cd skills/dan/scripts
python3 dan.py demo            # cuplikan sub-skill 01-21, ±30 detik
python3 dan.py demo --only 01,03,07   # fokus sesuai peran Anda
```

## 3. Peta kemampuan (2 menit)
- Baca `README-DAN.md` bagian "Isi paket" & "Engine yang bisa dijalankan".
- Routing permintaan → sub-skill: `skills/dan/SKILL.md` tabel §1.

## 4. Pasang di alat Anda (2 menit)
- Lihat `PLUGPLAY.md`: Claude / Cursor / Gemini / ChatGPT / Copilot / Windsurf / Zed /
  Continue / n8n / AGENTS.md / MCP.
- Verifikasi pemasangan: `python3 make_adapters.py validate` → 0 masalah.

## 5. Pakai untuk kerja nyata (sisanya)
- Data kampanye → `dan_analytics.py` → `make_infographic.py`.
- Proyek berjalan → `weekly_run.py` + `pmo_guard.py` + `weekly_diff.py`.
- Bangunan/denah → `arch_design.py`; prompt & kreatif → `storyboard.py`, `prompt_lab.py`.
- Selalu akhiri dengan QA: `_test_all.py` (0 gagal) & `run_cases.py run all`.

## Aturan main (wajib diingat)
1. Data dulu, opini kemudian; angka tertelusur atau ditandai `asumsi:`.
2. Setiap temuan = satu aksi terukur + tenggat.
3. Keluaran untuk keputusan harus lolos QA & guard.
4. Ragus? Tanya paket: `python3 rag.py query "…"` (jawaban bersitasi).

## Bantuan
- Tur ulang kapan pun: `dan.py demo`.
- Digest perubahan rilis: `make_digest.py` (+ naskah audio otomatis).
- Masalah pemasangan lintas AI: bagian 7–8 `PLUGPLAY.md`.
