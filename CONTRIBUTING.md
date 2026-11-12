# Contributing to TM Second Brain

Thank you for contributing to `tm-second-brain`!

## Guidelines
1. **License Compatibility:** All contributions must be original work compatible with the **MIT License**. Do not introduce GPL or Apache-2.0 files into the MIT core without maintainer approval.
2. **Minimal Dependencies:** Keep `tm_second_brain/core/` and `tm_second_brain/memory/` pure Python 3.10+ standard library.
3. **Cross-Platform:** Every feature must work on Linux, macOS, and Windows (use `pathlib.Path`, avoid POSIX-only shell assumptions).
4. **Tests:** Add deterministic `pytest` unit tests for all new behavior.
5. **Multilingual Docs:** Update `README.md` and keep `docs/{fa,tr,az,ar}/README.md` synchronized for user-facing changes.
