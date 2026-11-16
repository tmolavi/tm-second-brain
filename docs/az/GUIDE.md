# TM Second Brain — Tam İstifadəçi və İnteqrasiya Bələdçisi (`az`)

> [English](../en/GUIDE.md) · [فارسی](../fa/GUIDE.md) · [Türkçe](../tr/GUIDE.md) · [Azərbaycan README](README.md) · [العربية](../ar/GUIDE.md)

---

## 1. Quraşdırma Təlimatları

```bash
git clone https://github.com/tmolavi/tm-second-brain.git
cd tm-second-brain
python3 -m pip install -e .
```

Məcburi xarici asılılıq yoxdur. Python 3.10+ ilə **Linux, macOS və Windows** sistemlərində işləyir.

## 2. Konfiqurasiya

Üç hazır şablondan biri ilə (`personal-knowledge`, `business-project`, `developer-agent`) kassa yaradın:

```bash
tm-brain --vault ./my-vault init --template developer-agent
```

İstəyə bağlı semantik adapterlər (`QMDRetrievalAdapter`, `OllamaRetrievalAdapter`) standart olaraq **söndürülüb** və heç vaxt yeni model və ya işləmə mühiti quraşdırmır.

## 3. Arxitektura

1. **Qat 1 (Kanonik Saxlama):** `memories/` altında Markdown + YAML frontmatter + wikilink-lər, `working-dir/agent-log/` altında fəaliyyət jurnalları və yenidən qurula bilən SQLite FTS5 keşi `.tm-brain/index.db` (WAL rejimi).
2. **Qat 2 (Saf Python Nüvəsi):** Yaddaş həyat dövrü (`draft` → `active` → `superseded` → `archived`), mənşə izlənməsi, toqquşma aşkarlanması, layihə/mühit izolyasiyası, BM25 + qraf hibrid axtarış, L1→L2 öyrənmə qapısı və SHA-256 ehtiyat nüsxə/bərpa.
3. **Qat 3 (Adapterlər və Orkestrasiya):** Obsidian, stdio MCP (`tm-brain mcp`), kodlaşdırma agentləri (`codex`, `claude-code`, `gemini-cli`, `opencode`, `goose`, `antigravity`), orkestrasiya bacarığı (`tm-agent-orchestration`) və dörd izolyasiya olunmuş TM hədəfi (`hamzad-core`, `main-hermes`, `hermes-personal-desktop-finland`, `hermes-personal-desktop-mac`).

## 4. İstifadə Nümunələri

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

## 5. Agent İnteqrasiyaları

```bash
tm-brain --vault ./my-vault install-adapter codex
tm-brain --vault ./my-vault install-adapter claude-code
tm-brain --vault ./my-vault install-adapter gemini-cli
tm-brain --vault ./my-vault mcp
```

## 6. Təhlükəsizlik və Məxfilik

* `private: true` nişanlı və ya `private_paths` altındakı qeydlər MCP cavablarından, mühitlərarası sinxronizasiyadan və standart ixracdan kənarlaşdırılır.
* Məlum API açarları və tokenlər (`sk-*`, `ghp_*`, `AIza*`, `xoxb-*`, gizli açarlar) avtomatik maskalanır.
* `restore_backup(..., overwrite=True)` üzərinə yazmazdan əvvəl `pre-restore-*.tar.gz` təhlükəsizlik nüsxəsi yaradır.

## 7. Problemlərin Həlli

* **Axtarış nəticəsi yoxdur:** `--project` izolyasiyasını yoxlayın; `scope: project` yaddaşları yalnız öz layihələri ilə uyğunlaşır.
* **Windows fayl adı xətaları:** `sanitize_slug` qorunan adları (`CON`, `PRN`, `AUX`, `NUL`, `COM1–9`, `LPT1–9`) avtomatik yenidən yazır.

## 8. Töhfə Qaydaları

[`CONTRIBUTING.md`](../../CONTRIBUTING.md) faylına baxın. Bütün töhfələr MIT uyğun, nüvədə asılılıqsız, çarpaz-platformalı və `pytest` testləri ilə əhatə olunmalıdır.
