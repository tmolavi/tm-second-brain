[English](../../README.md) | [فارسی](../fa/README.md) | [Türkçe](../tr/README.md) | **Azərbaycan dili** | [العربية](../ar/README.md)

# TM İkinci Beyin (`tm-second-brain`)

> **TM / Molavi Agentic OS ekosistemi üçün orijinal, modul, çoxdilli və agentdən asılı olmayan İkinci Beyin və Davamlı Yaddaş sistemi.**

---

## 1. Ümumi Baxış və Əsas İmkanlar

`tm-second-brain` süni intellekt kodlaşdırma agentləri və komandalar üçün macOS, Linux və Windows üzərində tam oflayn və **$0.00 xərclə** işləyən **yerli-əsaslı (local-first) Markdown yaddaş sistemi** təqdim edir:

* **Sessiyalararası Davamlı Yaddaş:** Həyat dövrü statusları (`draft` → `active` → `superseded` → `archived`) olan Markdown + YAML frontmatter qeydləri.
* **Mənşə, Toqquşma Aşkarlanması və Düzəliş Tarixçəsi:** Məlumatların üzərinə səssizcə yazmır; əvvəlki versiyaları `supersedes` / `superseded_by` zənciri və `.tm-brain/corrections.jsonl` jurnalı ilə qoruyur.
* **Layihə və Mühit İzolyasiyası:** Layihələr arasında, həmçinin **Hamzad Core**, **Main Hermes** və **Hermes Personal Desktop** arasında ciddi izolyasiya.
* **Ödənişsiz Oflayn Axtarış:** Daxili Python BM25 + wikilink qraf genişlənməsi (`expand`) və istəyə bağlı QMD/Ollama dəstəyi.
* **Portativ Agent Orkestrasiyası (`tm-agent-orchestration`):** AutoSwarm prinsiplərindən ilhamlanan çoxagentli tapşırıq bölgüsü, paralel DAG icrası, gizli məlumatların maskalanması, sessiya bərpası və insan təsdiq qapıları.
* **Məxfilik və Gizli Məlumatların Maskalanması:** `private: true` / `private_paths` istisnası və MCP/ixrac zamanı API açarlarının maskalanması.
* **Təhlükəsiz Ehtiyat Nüsxə və Bərpa:** SHA-256 doğrulamalı `.tar.gz` arxivləri.

---

## 2. Üç Hazır Başlanğıc Şablonu

| Şablon | İstifadə Sahəsi | Əsas Struktur |
|---|---|---|
| `personal-knowledge` | Şəxsi Bilik Bazası | PARA (`00_Inbox`–`04_Archive`), `Daily Notes/`, gizli `02_Areas/Personal/` |
| `business-project` | Biznes və Layihələr | 3 İllik → Həftəlik Hədəf Zənciri, `Projects/`, `Meetings/`, `Decisions/`, `Home.base` |
| `developer-agent` | Tərtibatçı və Agentlər | `brain/`, `Skills/` (`SKILL.md` + `FEEDBACK.md`), `Knowledge Graph.canvas` |

---

## 3. Ekosistem və Adapter Dəstəyi

* **Obsidian:** Təhlükəsiz `.md` oxuma/yazma (üzərinə yazmadan əvvəl avtomatik ehtiyat nüsxə), YAML frontmatter, wikilink-lər və `.base`/`.canvas` qorunması.
* **Birinci Dərəcəli TM Hədəfləri:** **Hamzad Core** (`HamzadBridge`), **Main Hermes** (`MainHermesAdapter`) və **Hermes Personal Desktop** (`HermesPersonalDesktopAdapter`).
* **Kodlaşdırma Agentləri:** OpenAI Codex, Claude Code, Gemini CLI, OpenCode, Goose, Antigravity və stdio **MCP Server** (`tm-brain mcp`).

---

## 4. Sürətli Başlanğıc

```bash
python3 -m tm_second_brain.cli --vault ./my-vault init --template developer-agent
python3 -m tm_second_brain.cli --vault ./my-vault remember --title "Use WAL mode" --body "Enable SQLite WAL." --project core
python3 -m tm_second_brain.cli --vault ./my-vault search "WAL" --project core
python3 -m tm_second_brain.cli --vault ./my-vault install-adapter codex
python3 -m tm_second_brain.cli --vault ./my-vault orchestrate list
python3 -m tm_second_brain.cli --vault ./my-vault backup ./vault-backup.tar.gz
```

---

## 5. Memarlıq, Bacarıqlar və Lisenziya

* **Agent Orkestrasiyası Bacarığı:** [`skills/tm-agent-orchestration/SKILL.md`](../../skills/tm-agent-orchestration/SKILL.md) — AutoSwarm prinsipli çoxagentli koordinasiya.
* **Memarlıq və Müqavilələr:** [`ARCHITECTURE.md`](../../ARCHITECTURE.md), [`API-SPEC.md`](../../API-SPEC.md), [`ADAPTER-CONTRACTS.md`](../../ADAPTER-CONTRACTS.md) və [`INTEGRATION-SPEC.md`](../../INTEGRATION-SPEC.md)
* **Model və Xərc Şəffaflığı:** [`MODEL-REQUIREMENTS.md`](../../MODEL-REQUIREMENTS.md)
* **Lisenziya:** MIT License — [`LICENSE`](../../LICENSE) və [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)

---

## 6. Ətraflı Bələdçilər və Məqalələr

* **Molavi.pro (Azərbaycan dili):** [TM Second Brain Nədir? İnsanlar və Süni İntellekt Agentləri Üçün Davamlı Yaddaş Bələdçisi](https://molavi.pro/az/notes/tm-second-brain-persistent-memory)
* **Inten (English Guide):** [Why Your AI Sales & Engineering Stack Forgets Everything Overnight—And How TM Second Brain Fixes It at $0.00](https://inten.asia/blog/tm-second-brain-persistent-memory-en)
