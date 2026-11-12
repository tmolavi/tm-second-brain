"""Safe export/import and SHA-256 verified backup/restore for TM Second Brain."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from ..core.models import MemoryRecord, utc_now_iso
from ..memory.markdown_store import (
    MarkdownMemoryStore,
    atomic_write_text,
    serialize_memory_markdown,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_safe_archive_member(name: str) -> bool:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts:
        return False
    return True


class VaultBackupManager:
    """Implements BackupManager with non-destructive restore and SHA-256 verification."""

    def __init__(self, store: MarkdownMemoryStore) -> None:
        self.store = store

    def export_bundle(
        self, out_path: Path | str, *, include_private: bool = False
    ) -> dict[str, Any]:
        """Export memories to a portable JSON bundle, excluding private notes by default."""
        records = self.store._load_all_records()
        exported = [
            rec.to_dict()
            for rec in records
            if include_private or not self.store.privacy.is_private(rec)
        ]
        for item in exported:
            item["body"] = self.store.privacy.redact(item["body"])

        payload = {
            "schema_version": "1.0",
            "exported_at": utc_now_iso(),
            "count": len(exported),
            "records": exported,
        }
        raw = json.dumps(payload, indent=2, ensure_ascii=False)
        out = Path(out_path)
        atomic_write_text(out, raw)
        return {"path": str(out), "count": len(exported)}

    def import_bundle(
        self, bundle_path: Path | str, *, overwrite: bool = False
    ) -> dict[str, Any]:
        """Import memories from a JSON bundle idempotently."""
        data = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
        existing_ids = {r.id for r in self.store._load_all_records()}
        imported = 0
        skipped = 0

        for item in data.get("records", []):
            rec = MemoryRecord.from_dict(item)
            if rec.id in existing_ids and not overwrite:
                skipped += 1
                continue
            target = self.store._target_path(rec)
            rec.relative_path = target.relative_to(self.store.vault_root).as_posix()
            atomic_write_text(target, serialize_memory_markdown(rec))
            imported += 1

        return {"imported": imported, "skipped": skipped}

    def create_backup(self, archive_path: Path | str) -> dict[str, Any]:
        """Archive memories/ and .tm-brain/ with a SHA-256 manifest."""
        out = Path(archive_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        files_meta: dict[str, str] = {}
        sources: list[tuple[Path, str]] = []

        for root_dir in (self.store.memories_dir, self.store.meta_dir):
            if not root_dir.exists():
                continue
            for file_path in sorted(root_dir.rglob("*")):
                if file_path.is_file() and not file_path.name.startswith("pre-restore-"):
                    rel = file_path.relative_to(self.store.vault_root).as_posix()
                    sources.append((file_path, rel))

        with tarfile.open(out, "w:gz") as tar:
            for file_path, rel in sources:
                raw = file_path.read_bytes()
                files_meta[rel] = _sha256_bytes(raw)
                info = tarfile.TarInfo(name=rel)
                info.size = len(raw)
                tar.addfile(info, io.BytesIO(raw))

            manifest = {
                "schema_version": "1.0",
                "created_at": utc_now_iso(),
                "files": files_meta,
            }
            manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
            m_info = tarfile.TarInfo(name="backup-manifest.json")
            m_info.size = len(manifest_bytes)
            tar.addfile(m_info, io.BytesIO(manifest_bytes))

        return {"archive": str(out), "file_count": len(files_meta)}

    def restore_backup(
        self, archive_path: Path | str, *, overwrite: bool = False
    ) -> dict[str, Any]:
        """Verify SHA-256 checksums and restore files without clobbering existing ones by default."""
        arc = Path(archive_path)
        restored = 0
        skipped = 0
        snapshot_path: str | None = None

        if overwrite:
            ts = utc_now_iso().replace(":", "").replace("-", "")
            snap = self.store.meta_dir / f"pre-restore-{ts}.tar.gz"
            self.create_backup(snap)
            snapshot_path = str(snap)

        with tarfile.open(arc, "r:gz") as tar:
            members = tar.getmembers()
            for member in members:
                if not _is_safe_archive_member(member.name):
                    raise ValueError(f"Unsafe archive path: {member.name}")

            manifest_member = tar.getmember("backup-manifest.json")
            manifest_f = tar.extractfile(manifest_member)
            if manifest_f is None:
                raise ValueError("Missing backup-manifest.json")
            manifest = json.loads(manifest_f.read().decode("utf-8"))
            expected_hashes: dict[str, str] = manifest.get("files", {})

            for rel, expected_sha in expected_hashes.items():
                if not _is_safe_archive_member(rel):
                    raise ValueError(f"Unsafe manifest path: {rel}")
                member = tar.getmember(rel)
                extracted = tar.extractfile(member)
                if extracted is None:
                    continue
                raw = extracted.read()
                if _sha256_bytes(raw) != expected_sha:
                    raise ValueError(f"Checksum mismatch for {rel}")

                dest = (self.store.vault_root / rel).resolve()
                if self.store.vault_root not in dest.parents:
                    raise ValueError(f"Path traversal detected: {rel}")
                if dest.exists() and not overwrite:
                    skipped += 1
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(raw)
                restored += 1

        return {"restored": restored, "skipped": skipped, "pre_restore_snapshot": snapshot_path}
