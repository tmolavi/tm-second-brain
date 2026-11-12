[English](../../README.md) | [فارسی](../fa/README.md) | **Türkçe** | [Azərbaycan dili](../az/README.md) | [العربية](../ar/README.md)

# TM İkinci Beyin (`tm-second-brain`)

> **TM / Molavi Agentic OS ekosistemi için özgün, modüler, çok dilli ve ajandan bağımsız İkinci Beyin ve Kalıcı Bellek sistemi.**

---

## 1. Genel Bakış ve Temel Özellikler

`tm-second-brain`, yapay zeka kodlama ajanları ve ekipler için macOS, Linux ve Windows üzerinde tamamen çevrimdışı ve **$0.00 maliyetle** çalışan **yerel öncelikli (local-first) Markdown tabanlı kalıcı bellek** sunar:

* **Oturumlar Arası Kalıcı Bellek:** Yaşam döngüsü durumlarına (`draft` → `active` → `superseded` → `archived`) sahip Markdown + YAML frontmatter kayıtları.
* **Kaynak, Çakışma Tespiti ve Düzeltme Geçmişi:** Gerçeklerin üzerine sessizce yazmaz; önceki sürümleri `supersedes` / `superseded_by` zinciri ve `.tm-brain/corrections.jsonl` günlüğü ile korur.
* **Proje ve Ortam İzolasyonu:** Projeler arasında ve **Hamzad Core**, **Main Hermes** ile **Hermes Personal Desktop** arasında sıkı izolasyon.
* **Ücretsiz Çevrimdışı Arama:** Yerleşik Python BM25 + wikilink grafik genişletme (`expand`) ve isteğe bağlı QMD/Ollama desteği.
* **Gizlilik ve Sır Maskeleme:** `private: true` / `private_paths` dışlama ve MCP/dışa aktarım sınırlarında API anahtarı maskeleme.
* **Güvenli Yedekleme ve Geri Yükleme:** SHA-256 doğrulamalı `.tar.gz` yedekleri.

---

## 2. Üç Hazır Başlangıç Kasası (Starter Vault)

| Şablon | Kullanım Alanı | Temel Yapı |
|---|---|---|
| `personal-knowledge` | Kişisel Bilgi Yönetimi | PARA (`00_Inbox`–`04_Archive`), `Daily Notes/`, gizli `02_Areas/Personal/` |
| `business-project` | İş ve Proje Yönetimi | 3 Yıllık → Haftalık Hedef Zinciri, `Projects/`, `Meetings/`, `Decisions/`, `Home.base` |
| `developer-agent` | Geliştirici ve Ajanlar | `brain/`, `Skills/` (`SKILL.md` + `FEEDBACK.md`), `Knowledge Graph.canvas` |

---

## 3. Ekosistem ve Adaptör Desteği

* **Obsidian:** Güvenli `.md` okuma/yazma (üzerine yazmadan önce otomatik yedekleme), YAML frontmatter, wikilink ve `.base`/`.canvas` koruma.
* **Birinci Sınıf TM Hedefleri:** **Hamzad Core** (`HamzadBridge`), **Main Hermes** (`MainHermesAdapter`) ve **Hermes Personal Desktop** (`HermesPersonalDesktopAdapter`).
* **Kodlama Ajanları:** OpenAI Codex, Claude Code, Gemini CLI, OpenCode, Goose, Antigravity ve stdio **MCP Sunucusu** (`tm-brain mcp`).

---

## 4. Hızlı Başlangıç

```bash
python3 -m tm_second_brain.cli --vault ./my-vault init --template developer-agent
python3 -m tm_second_brain.cli --vault ./my-vault remember --title "Use WAL mode" --body "Enable SQLite WAL." --project core
python3 -m tm_second_brain.cli --vault ./my-vault search "WAL" --project core
python3 -m tm_second_brain.cli --vault ./my-vault install-adapter codex
python3 -m tm_second_brain.cli --vault ./my-vault backup ./vault-backup.tar.gz
```

---

## 5. Lisans ve Model Şeffaflığı

* **Model ve Maliyet Şeffaflığı:** [`MODEL-REQUIREMENTS.md`](../../MODEL-REQUIREMENTS.md)
* **Lisans:** MIT License — [`LICENSE`](../../LICENSE) ve [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)
