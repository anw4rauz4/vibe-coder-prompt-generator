---
name: dan-rag-retrieval
description: >-
  Retrieval Augmented Generation tanpa dependensi: mengindeks dokumen Markdown menjadi
  chunk ber-heading, retrieval TF-IDF + cosine, jawaban dengan SITASI file+heading,
  serta evaluasi retrieval (recall@k manual). Jujur tentang batas lexical vs embedding.
  Gunakan saat pengguna meminta "tanya dokumen saya", "basis pengetahuan internal",
  "jawab dengan rujukan", chatbot dokumen, atau mengurangi hallucination dengan grounding.
---

# 13 · Retrieval Augmented Generation (RAG)

## Prinsip
1. **Grounding dulu, generasi kemudian**: setiap jawaban menyebut sumber chunk-nya.
2. Retrieval lexical (TF-IDF/BM25) sudah cukup untuk dokumen teknis beristilah pasti;
   naik ke embedding hanya bila sinonim/parafrase sering gagal (ukur, jangan asumsi).
3. Chunk ber-heading + sitasi membuat kesalahan retrieval MUDAH diperiksa manusia.

## Perintah
```bash
cd skills/dan/scripts
python3 rag.py index --roots skills/dan --out deliverables/rag_index.json
python3 rag.py query "ambang waspada variance proyek?" --top 4
python3 rag.py query "..." --index deliverables/rag_index.json   # pakai indeks tersimpan
```

## Pipeline
```
md files -> chunk (split per heading, ≤900 char) -> tokenize (stopwords ID/EN)
        -> tf-idf (log-tf × idf, L2-normalized) -> cosine top-k -> sitasi
```

## Checklist kualitas RAG
- [ ] recall@5 diuji pada ≥10 pertanyaan nyata (tandai relevan/tidak per chunk)
- [ ] pertanyaan tanpa jawaban di korpus → sistem berani bilang "tidak ada di dokumen"
- [ ] chunk tidak memotong tabel/kode di tengah (periksa chunk berisi `|---|`)
- [ ] sitasi menampilkan file + heading, bukan hanya skor
- [ ] indeks di-refresh saat dokumen berubah (jadwalkan bersama workflow, sub-skill 11)

## Kapan naik kelas
| Gejala | Tindakan |
|---|---|
| Sinonim/parafrase sering miss | tambah embedding (opsional) sebagai re-ranker |
| Jawaban perlu lintas banyak chunk | tambah tahap "merge & summarize" setelah retrieval |
| Korpus >100k chunk | pindah ke vector DB (sub-skill 17: qdrant/pgvector) |

## Integrasi
- Sumber korpus default: seluruh `skills/dan/**/*.md` (paket ini) — agent bisa
  "menanya dirinya sendiri".
- Gabungkan dengan claim_audit (sub-skill QA): angka dari jawaban RAG tetap diaudit.
