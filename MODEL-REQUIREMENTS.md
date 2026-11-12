# Model, API & Cost Transparency (`MODEL-REQUIREMENTS.md`)

> **Standard:** TM Open Source Standard §4  
> **Default Execution Cost:** **$0.00** (zero mandatory LLM or embedding API calls)

---

## 1. Zero-Cost Default Operation

`tm-second-brain` is **local-first and free-first**:
* **Core Memory, Lifecycle, Conflict History, Privacy Redaction, Backup, and BM25 + Graph Retrieval** run 100% locally in pure Python 3.10+ with **zero LLM tokens** and **zero API keys**.

## 2. Optional Model & Embedding Providers

| Tier | Provider | Recommended Models | Token / Compute Budget | Cost |
|---|---|---|---|---|
| **Tier 0 (Default)** | Built-in Python BM25 + SQLite FTS5 + Graph | None (deterministic) | 0 tokens | **$0.00** |
| **Tier 1 (Local Semantic)** | `@tobilu/qmd` | `embeddinggemma-300M` (~328 MB), `qmd-query-expansion-1.7B` (~1.28 GB), `Qwen3-Reranker-0.6B` (~640 MB) | Local CPU/Metal/CUDA | **$0.00** |
| **Tier 1 (Local Embeddings/LLM)** | Ollama (`localhost:11434`) | `nomic-embed-text`, `llama3.2`, `qwen2.5` | Local hardware | **$0.00** |
| **Tier 2 (Zero-Cost Cloud)** | Google Gemini Free Tier / Groq Free Tier | `gemini-2.5-flash`, `llama-3.3-70b-versatile` | ~500–2,000 tokens/query (optional) | **$0.00** (rate-limited free tier) |
| **Tier 3 (Paid Cloud, Opt-In)** | Anthropic / OpenAI | User-configured | Explicit opt-in only | Paid by user |

**Policy:** `tm-second-brain` never silently escalates to paid cloud APIs, and never sends `private: true` or excluded paths to any external provider.
