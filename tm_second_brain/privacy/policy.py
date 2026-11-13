"""Privacy policy enforcement and secret/PII redaction."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Iterable

from ..core.models import MemoryRecord

_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"sk-[A-Za-z0-9_-]{16,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{20,}"), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._\-]{16,}"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(password|secret|api_key|token)\s*[:=]\s*['\"]?(?!\[REDACTED_)([A-Za-z0-9!@#$%^&*()_+=\-`~|:;<>?,./]{6,})['\"]?"), r"\1=[REDACTED_SECRET]"),
)

DEFAULT_PRIVATE_PATHS: tuple[str, ...] = (
    "Areas/Personal/",
    "private/",
    "memories/private/",
)


class DefaultPrivacyPolicy:
    """Filters private notes and redacts sensitive credentials."""

    def __init__(self, private_paths: Iterable[str] = DEFAULT_PRIVATE_PATHS) -> None:
        self.private_paths = tuple(
            p.replace("\\", "/").strip("/") + "/" for p in private_paths if p.strip("/")
        )

    def is_private(self, record: MemoryRecord) -> bool:
        """Return True if the record is marked private or resides in a private folder."""
        if record.private:
            return True
        if not record.relative_path:
            return False
        norm = PurePosixPath(record.relative_path.replace("\\", "/")).as_posix().lstrip("/")
        return any(norm.startswith(prefix) for prefix in self.private_paths)

    def redact(self, text: str) -> str:
        """Scrub known secret patterns from text."""
        result = text
        for pattern, replacement in _SECRET_PATTERNS:
            result = pattern.sub(replacement, result)
        return result
