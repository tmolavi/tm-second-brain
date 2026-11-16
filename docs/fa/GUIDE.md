<div dir="rtl">

# راهنمای کامل کاربری و یکپارچه‌سازی TM Second Brain (`fa`)

> [English](../en/GUIDE.md) · [README فارسی](README.md) · [Türkçe](../tr/GUIDE.md) · [Azərbaycan dili](../az/GUIDE.md) · [العربية](../ar/GUIDE.md)

---

## ۱. دستورالعمل نصب

```bash
git clone https://github.com/tmolavi/tm-second-brain.git
cd tm-second-brain
python3 -m pip install -e .
```

بدون نیاز به وابستگی خارجی اجباری. روی **Linux، macOS و Windows** با Python 3.10+ به‌صورت بومی اجرا می‌شود.

## ۲. پیکربندی

ایجاد یک Vault جدید با یکی از سه قالب آماده (`personal-knowledge`، `business-project`، `developer-agent`):

```bash
tm-brain --vault ./my-vault init --template developer-agent
```

آداپتورهای معنایی اختیاری (`QMDRetrievalAdapter` و `OllamaRetrievalAdapter`) به‌صورت پیش‌فرض **غیرفعال** هستند و هرگز مدل یا ابزار جدیدی نصب نمی‌کنند.

## ۳. معماری سیستم

۱. **لایه ۱ (ذخیره‌سازی استاندارد):** فایل‌های Markdown + YAML frontmatter + ویکی‌لینک‌ها در `memories/`، لاگ فعالیت در `working-dir/agent-log/` و کش قابل بازسازی SQLite FTS5 در `.tm-brain/index.db` (حالت WAL).
۲. **لایه ۲ (هسته خالص پایتون):** چرخه حیات حافظه (`draft` → `active` → `superseded` → `archived`)، منشأ، تشخیص تعارض، جداسازی پروژه و محیط، بازیابی ترکیبی BM25 + گراف، دروازه یادگیری L1→L2 و پشتیبان‌گیری SHA-256.
۳. **لایه ۳ (آداپتورها و ارکستراسیون):** Obsidian، سرور MCP (`tm-brain mcp`)، ایجنت‌های کدنویسی (`codex`، `claude-code`، `gemini-cli`، `opencode`، `goose`، `antigravity`)، مهارت ارکستراسیون (`tm-agent-orchestration`) و چهار هدف مجزای TM (`hamzad-core`، `main-hermes`، `hermes-personal-desktop-finland`، `hermes-personal-desktop-mac`).

## ۴. نمونه‌های استفاده

```bash
tm-brain --vault ./my-vault remember --title "WAL Mode" --body "Enable SQLite WAL." --project core --confidence verified --verification "pytest"
tm-brain --vault ./my-vault search "WAL" --project core
tm-brain --vault ./my-vault correct mem_20261112_abc123 --title "WAL Mode" --body "Enable WAL + synchronous=NORMAL." --reason "Throughput tuning"
tm-brain --vault ./my-vault orchestrate list
tm-brain --vault ./my-vault orchestrate status sess_001
tm-brain --vault ./my-vault learn log --skill code-review --outcome missed --rule "Check empty inputs"
tm-brain --vault ./my-vault learn scan --min-occurrences 2
tm-brain --vault ./my-vault backup ./backup.tar.gz
```

## ۵. یکپارچه‌سازی با ایجنت‌ها

```bash
tm-brain --vault ./my-vault install-adapter codex
tm-brain --vault ./my-vault install-adapter claude-code
tm-brain --vault ./my-vault install-adapter gemini-cli
tm-brain --vault ./my-vault mcp
```

## ۶. امنیت و حریم خصوصی

* یادداشت‌های دارای `private: true` یا واقع در `private_paths` از پاسخ‌های MCP، همگام‌سازی بین‌محیطی و خروجی پیش‌فرض حذف می‌شوند.
* کلیدهای API و توکن‌ها (`sk-*`، `ghp_*`، `AIza*`، `xoxb-*`، کلیدهای خصوصی) به‌صورت خودکار سانسور می‌شوند.
* دستور `restore_backup(..., overwrite=True)` پیش از بازنویسی، یک اسنپ‌شات ایمنی `pre-restore-*.tar.gz` ایجاد می‌کند.

## ۷. عیب‌یابی

* **عدم نمایش نتیجه در جستجو:** مقدار `--project` را بررسی کنید؛ حافظه‌های `scope: project` تنها برای پروژه‌های مجاز خودشان بازگردانده می‌شوند.
* **خطای نام فایل در ویندوز:** تابع `sanitize_slug` نام‌های رزروشده (`CON`، `PRN`، `AUX`، `NUL`، `COM1–9`، `LPT1–9`) را خودکار اصلاح می‌کند.

## ۸. راهنمای مشارکت

به [`CONTRIBUTING.md`](../../CONTRIBUTING.md) مراجعه کنید. تمام مشارکت‌ها باید با مجوز MIT سازگار، بدون وابستگی اجباری در هسته، چندسکویی و دارای تست `pytest` باشند.

</div>
