[English](../../README.md) | **فارسی** | [Türkçe](../tr/README.md) | [Azərbaycan dili](../az/README.md) | [العربية](../ar/README.md)

# مغز دوم تی‌ام (`tm-second-brain`)

> **یک سیستم مغز دوم و حافظه ماندگارِ ماژولار، چندزبانه و مستقل از ایجنت برای اکوسیستم TM / Molavi Agentic OS.**

---

## ۱. معرفی و قابلیت‌های کلیدی

`tm-second-brain` یک **حافظه ماندگار محلی (Local-First) بر پایه Markdown** برای ایجنت‌های کدنویسی و تیم‌های انسانی فراهم می‌کند که به‌صورت کاملاً آفلاین و با **هزینه ۰.۰۰ دلار** روی macOS، Linux و Windows اجرا می‌شود:

* **حافظه ماندگار بین جلسات:** ذخیره در Markdown + YAML frontmatter با چرخه حیات کامل (`draft` → `active` → `superseded` → `archived`).
* **منشأ، تشخیص تعارض و تاریخچه اصلاحات:** هرگز داده‌ها را بی‌صدا بازنویسی نمی‌کند؛ نسخه‌های قبلی با زنجیره `supersedes` / `superseded_by` و فایل ثبت اصلاحات (`.tm-brain/corrections.jsonl`) حفظ می‌شوند.
* **جداسازی پروژه و محیط‌ها:** جداسازی دقیق بین پروژه‌ها و همچنین بین **Hamzad Core**، **Main Hermes** و **Hermes Personal Desktop**.
* **بازیابی آفلاین رایگان:** موتور داخلی BM25 + گسترش گراف لینک‌های ویکی (`expand`)، همراه با رابط قابل تعویض برای QMD یا Ollama.
* **حریم خصوصی و سانسور اسرار:** حذف خودکار یادداشت‌های `private: true` و پنهان‌سازی کلیدهای API و توکن‌ها در MCP، خروجی‌ها و پل‌ها.
* **پشتیبان‌گیری و بازیابی امن:** آرشیو `.tar.gz` با راستی‌آزمایی SHA-256 و اسنپ‌شات ایمنی پیش از بازنویسی.

---

## ۲. سه قالب آماده Vault

| قالب | مناسب برای | ساختار کلیدی |
|---|---|---|
| `personal-knowledge` | دانش شخصی (PKM) | ساختار PARA، یادداشت‌های روزانه، پوشه خصوصی `02_Areas/Personal/` |
| `business-project` | کسب‌وکار و پروژه | آبشار اهداف ۳ ساله تا هفتگی، پروژه‌ها، جلسات، تصمیمات، `Home.base` |
| `developer-agent` | توسعه‌دهندگان و ایجنت‌ها | `brain/`، مهارت‌ها (`SKILL.md` + `FEEDBACK.md`)، گراف `Knowledge Graph.canvas` |

---

## ۳. پشتیبانی از اکوسیستم و آداپتورها

* **Obsidian:** خواندن و نوشتن امن `.md` (پشتیبان‌گیری خودکار پیش از بازنویسی)، YAML frontmatter، ویکی‌لینک‌ها و حفظ فایل‌های `.base` و `.canvas`.
* **اهداف درجه یک TM (کاملاً مجزا):** **Hamzad Core** (`HamzadBridge`)، **Main Hermes** (`MainHermesAdapter`) و **Hermes Personal Desktop** (`HermesPersonalDesktopAdapter`).
* **ایجنت‌های کدنویسی:** OpenAI Codex، Claude Code، Gemini CLI، OpenCode، Goose، Antigravity و سرور استاندارد **MCP** (`tm-brain mcp`).

---

## ۴. شروع سریع

```bash
python3 -m tm_second_brain.cli --vault ./my-vault init --template developer-agent
python3 -m tm_second_brain.cli --vault ./my-vault remember --title "Use WAL mode" --body "Enable SQLite WAL." --project core
python3 -m tm_second_brain.cli --vault ./my-vault search "WAL" --project core
python3 -m tm_second_brain.cli --vault ./my-vault install-adapter codex
python3 -m tm_second_brain.cli --vault ./my-vault backup ./vault-backup.tar.gz
```

---

## ۵. مجوز و شفافیت مدل‌ها

* **شفافیت مدل و هزینه:** [`MODEL-REQUIREMENTS.md`](../../MODEL-REQUIREMENTS.md)
* **مجوز انتشار:** MIT License — [`LICENSE`](../../LICENSE) و [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)

---

## ۶. راهنماها و مقالات جامع (فارسی)

* **مولوی‌پرو (راهنمای جامع):** [TM Second Brain چیست؟ راهنمای کامل حافظه دائمی و مغز دوم برای انسان‌ها و ایجنت‌های هوش مصنوعی](https://molavi.pro/fa/notes/tm-second-brain-persistent-memory)
* **اینتن (معماری حافظه برند و تیم فروش):** [چرا هوش مصنوعی کسب‌وکارتان هر روز حافظه‌اش را از دست می‌دهد؟ معرفی TM Second Brain](https://inten.asia/blog/tm-second-brain-persistent-memory)
