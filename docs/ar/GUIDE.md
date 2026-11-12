<div dir="rtl">

# الدليل الكامل للاستخدام والتكامل لنظام TM Second Brain (`ar`)

> [English](../en/GUIDE.md) · [فارسی](../fa/GUIDE.md) · [Türkçe](../tr/GUIDE.md) · [Azərbaycan dili](../az/GUIDE.md) · [العربية README](README.md)

---

## ١. تعليمات التثبيت

```bash
git clone https://github.com/tmolavi/tm-second-brain.git
cd tm-second-brain
python3 -m pip install -e .
```

بدون أي تبعيات خارجية إلزامية. يعمل على **Linux وmacOS وWindows** باستخدام Python 3.10+.

## ٢. الإعداد والتكوين

تهيئة خزنة باستخدام أحد القوالب الثلاثة الجاهزة (`personal-knowledge`، `business-project`، `developer-agent`):

```bash
tm-brain --vault ./my-vault init --template developer-agent
```

المحولات الدلالية الاختيارية (`QMDRetrievalAdapter` و`OllamaRetrievalAdapter`) **معطلة افتراضياً** ولا تقوم أبداً بتثبيت نماذج أو بيئات تشغيل جديدة.

## ٣. البنية المعمارية

١. **الطبقة ١ (التخزين القياسي):** ملفات Markdown + YAML frontmatter + روابط الويكي تحت `memories/`، وسجل النشاط في `working-dir/agent-log/`، وذاكرة تخزين مؤقت قابلة لإعادة البناء SQLite FTS5 في `.tm-brain/index.db` (وضع WAL).
٢. **الطبقة ٢ (النواة النقية بلغة Python):** دورة حياة الذاكرة (`draft` → `active` → `superseded` → `archived`)، والمصدر، وكشف التعارضات، وعزل المشاريع والبيئات، والبحث الهجين BM25 + الرسم البياني، وبوابة التعلم L1→L2، والنسخ الاحتياطي SHA-256.
٣. **الطبقة ٣ (المحولات):** Obsidian، وخادم MCP (`tm-brain mcp`)، ووكلاء البرمجة (`codex`، `claude-code`، `gemini-cli`، `opencode`، `goose`، `antigravity`)، وأربعة أهداف معزولة لمنظومة TM (`hamzad-core`، `main-hermes`، `hermes-personal-desktop-finland`، `hermes-personal-desktop-mac`).

## ٤. أمثلة الاستخدام

```bash
tm-brain --vault ./my-vault remember --title "WAL Mode" --body "Enable SQLite WAL." --project core --confidence verified --verification "pytest"
tm-brain --vault ./my-vault search "WAL" --project core
tm-brain --vault ./my-vault correct mem_20261112_abc123 --title "WAL Mode" --body "Enable WAL + synchronous=NORMAL." --reason "Throughput tuning"
tm-brain --vault ./my-vault learn log --skill code-review --outcome missed --rule "Check empty inputs"
tm-brain --vault ./my-vault learn scan --min-occurrences 2
tm-brain --vault ./my-vault backup ./backup.tar.gz
```

## ٥. تكامل الوكلاء

```bash
tm-brain --vault ./my-vault install-adapter codex
tm-brain --vault ./my-vault install-adapter claude-code
tm-brain --vault ./my-vault install-adapter gemini-cli
tm-brain --vault ./my-vault mcp
```

## ٦. الأمان والخصوصية

* الملاحظات الموسومة بـ `private: true` أو الموجودة تحت `private_paths` تُستبعد من استجابات MCP والمزامنة والتصدير الافتراضي.
* يتم تنقيح مفاتيح API والرموز (`sk-*`، `ghp_*`، `AIza*`، `xoxb-*`، المفاتيح الخاصة) تلقائياً.
* ينشئ `restore_backup(..., overwrite=True)` لقطة أمان `pre-restore-*.tar.gz` قبل الكتابة فوق الملفات.

## ٧. استكشاف الأخطاء وإصلاحها

* **لا توجد نتائج بحث:** تحقق من عزل `--project`؛ فذكريات `scope: project` لا تطابق إلا مشاريعها المحددة.
* **أخطاء أسماء الملفات في Windows:** تعيد دالة `sanitize_slug` تلقائياً تسمية الأسماء المحجوزة (`CON`، `PRN`، `AUX`، `NUL`، `COM1–9`، `LPT1–9`).

## ٨. إرشادات المساهمة

راجع [`CONTRIBUTING.md`](../../CONTRIBUTING.md). يجب أن تكون جميع المساهمات متوافقة مع رخصة MIT، وخالية من التبعيات الإلزامية في النواة، ومتعددة المنصات، ومغطاة باختبارات `pytest`.

</div>
