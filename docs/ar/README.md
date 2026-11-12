[English](../../README.md) | [فارسی](../fa/README.md) | [Türkçe](../tr/README.md) | [Azərbaycan dili](../az/README.md) | **العربية**

# الدماغ الثاني TM (`tm-second-brain`)

> **نظام دماغ ثانٍ وذاكرة دائمة أصلي ومعياري ومتعدد اللغات ومستقل عن الوكلاء لمنظومة TM / Molavi Agentic OS.**

---

## ١. نظرة عامة والميزات الرئيسية

يوفر `tm-second-brain` لوكلاء البرمجة والفرق البشرية **ذاكرة دائمة محلية أولاً (Local-First) تعتمد على Markdown** وتعمل دون اتصال بالإنترنت وبتكلفة **$0.00** على macOS وLinux وWindows:

* **ذاكرة دائمة عبر الجلسات:** ملفات Markdown + YAML frontmatter مع حالات دورة الحياة (`draft` → `active` → `superseded` → `archived`).
* **المصدر وكشف التعارضات وسجل التصحيحات:** لا يستبدل الحقائق بصمت أبداً؛ بل يحفظ الإصدارات السابقة عبر سلسلة `supersedes` / `superseded_by` وسجل `.tm-brain/corrections.jsonl`.
* **عزل المشاريع والبيئات:** عزل صارم بين المشاريع، وكذلك بين **Hamzad Core** و**Main Hermes** و**Hermes Personal Desktop**.
* **بحث محلي مجاني دون اتصال:** محرك BM25 مدمج بلغة Python + توسيع روابط الويكي (`expand`)، مع دعم اختياري لـ QMD وOllama.
* **الخصوصية وتنقيح الأسرار:** استبعاد الملاحظات الموسومة بـ `private: true` / `private_paths` وتنقيح مفاتيح API تلقائياً.
* **نسخ احتياطي واستعادة آمنة:** أرشيفات `.tar.gz` محققة ببصمة SHA-256.

---

## ٢. ثلاثة قوالب جاهزة للخزنة (Starter Vaults)

| القالب | الأنسب لـ | البنية الأساسية |
|---|---|---|
| `personal-knowledge` | المعرفة الشخصية | PARA (`00_Inbox`–`04_Archive`)، `Daily Notes/`، مجلد خاص `02_Areas/Personal/` |
| `business-project` | الأعمال والمشاريع | سلسلة الأهداف من ٣ سنوات إلى الأسبوعية، `Projects/`، `Meetings/`، `Decisions/`، `Home.base` |
| `developer-agent` | المطورون والوكلاء | `brain/`، المهارات (`SKILL.md` + `FEEDBACK.md`)، مخطط `Knowledge Graph.canvas` |

---

## ٣. دعم المنظومة والمحولات (Adapters)

* **Obsidian:** قراءة وكتابة آمنة لملفات `.md` (نسخ احتياطي تلقائي قبل الاستبدال)، YAML frontmatter، روابط ويكي، وحفظ `.base` و`.canvas`.
* **أهداف TM من الدرجة الأولى:** **Hamzad Core** (`HamzadBridge`)، **Main Hermes** (`MainHermesAdapter`)، و**Hermes Personal Desktop** (`HermesPersonalDesktopAdapter`).
* **وكلاء البرمجة:** OpenAI Codex، Claude Code، Gemini CLI، OpenCode، Goose، Antigravity، وخادم **MCP** (`tm-brain mcp`).

---

## ٤. البدء السريع

```bash
python3 -m tm_second_brain.cli --vault ./my-vault init --template developer-agent
python3 -m tm_second_brain.cli --vault ./my-vault remember --title "Use WAL mode" --body "Enable SQLite WAL." --project core
python3 -m tm_second_brain.cli --vault ./my-vault search "WAL" --project core
python3 -m tm_second_brain.cli --vault ./my-vault install-adapter codex
python3 -m tm_second_brain.cli --vault ./my-vault backup ./vault-backup.tar.gz
```

---

## ٥. الترخيص وشفافية النماذج

* **شفافية النماذج والتكلفة:** [`MODEL-REQUIREMENTS.md`](../../MODEL-REQUIREMENTS.md)
* **الترخيص:** MIT License — [`LICENSE`](../../LICENSE) و[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md)

---

## ٦. الأدلة والمقالات الشاملة

* **Molavi.pro (الدليل العربي):** [ما هو TM Second Brain؟ الدليل الشامل للذاكرة الدائمة والعقل الثاني للبشر ووكلاء الذكاء الاصطناعي](https://molavi.pro/ar/notes/tm-second-brain-persistent-memory)
* **Inten (English Guide):** [Why Your AI Sales & Engineering Stack Forgets Everything Overnight—And How TM Second Brain Fixes It at $0.00](https://inten.asia/blog/tm-second-brain-persistent-memory-en)
