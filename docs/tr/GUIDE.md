# TM Second Brain — Kapsamlı Kullanıcı ve Entegrasyon Kılavuzu (`tr`)

> [English](../en/GUIDE.md) · [فارسی](../fa/GUIDE.md) · [Türkçe README](README.md) · [Azərbaycan dili](../az/GUIDE.md) · [العربية](../ar/GUIDE.md)

---

## 1. Kurulum Talimatları

```bash
git clone https://github.com/tmolavi/tm-second-brain.git
cd tm-second-brain
python3 -m pip install -e .
```

Zorunlu harici bağımlılık yoktur. Python 3.10+ ile **Linux, macOS ve Windows** üzerinde çalışır.

## 2. Yapılandırma

Üç hazır şablondan biriyle (`personal-knowledge`, `business-project`, `developer-agent`) kasa başlatın:

```bash
tm-brain --vault ./my-vault init --template developer-agent
```

İsteğe bağlı semantik adaptörler (`QMDRetrievalAdapter`, `OllamaRetrievalAdapter`) varsayılan olarak **devre dışıdır** ve asla yeni çalışma zamanı veya model ağırlığı kurmaz.

## 3. Mimari

1. **Katman 1 (Kanonik Depolama):** `memories/` altında Markdown + YAML frontmatter + wikilink'ler, `working-dir/agent-log/` altında etkinlik günlükleri ve yeniden oluşturulabilir SQLite FTS5 önbelleği `.tm-brain/index.db` (WAL modu).
2. **Katman 2 (Saf Python Çekirdeği):** Bellek yaşam döngüsü (`draft` → `active` → `superseded` → `archived`), kaynak takibi, çakışma tespiti, proje/ortam izolasyonu, BM25 + grafik hibrit arama, L1→L2 öğrenme kapısı ve SHA-256 yedekleme/geri yükleme.
3. **Katman 3 (Adaptörler ve Orkestrasyon):** Obsidian, stdio MCP (`tm-brain mcp`), kodlama ajanları (`codex`, `claude-code`, `gemini-cli`, `opencode`, `goose`, `antigravity`), orkestrasyon becerisi (`tm-agent-orchestration`) ve dört izole TM hedefi (`hamzad-core`, `main-hermes`, `hermes-personal-desktop-finland`, `hermes-personal-desktop-mac`).

## 4. Kullanım Örnekleri

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

## 5. Ajan Entegrasyonları

```bash
tm-brain --vault ./my-vault install-adapter codex
tm-brain --vault ./my-vault install-adapter claude-code
tm-brain --vault ./my-vault install-adapter gemini-cli
tm-brain --vault ./my-vault mcp
```

## 6. Güvenlik ve Gizlilik

* `private: true` etiketli veya `private_paths` altındaki notlar MCP yanıtlarından, ortamlar arası aktarımdan ve varsayılan dışa aktarımlardan hariç tutulur.
* Bilinen API anahtarları ve belirteçler (`sk-*`, `ghp_*`, `AIza*`, `xoxb-*`, özel anahtarlar) otomatik olarak maskelenir.
* `restore_backup(..., overwrite=True)` üzerine yazmadan önce `pre-restore-*.tar.gz` güvenlik anlık görüntüsü oluşturur.

## 7. Sorun Giderme

* **Arama sonucu yok:** `--project` izolasyonunu kontrol edin; `scope: project` bellekleri yalnızca kendi projeleriyle eşleşir.
* **Windows dosya adı hataları:** `sanitize_slug` ayrılmış adları (`CON`, `PRN`, `AUX`, `NUL`, `COM1–9`, `LPT1–9`) otomatik olarak yeniden yazar.

## 8. Katkı Kuralları

[`CONTRIBUTING.md`](../../CONTRIBUTING.md) dosyasına bakın. Tüm katkılar MIT uyumlu, çekirdekte bağımlılıksız, çapraz platformlu ve `pytest` testleriyle kapsanmış olmalıdır.
