"""Negative security tests, backup/rollback verification, and starter vault template tests."""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest

from tm_second_brain.backup.archive import VaultBackupManager
from tm_second_brain.backup.templates import VALID_TEMPLATES, install_starter_template
from tm_second_brain.cli import main as cli_main
from tm_second_brain.core.models import MemoryScope
from tm_second_brain.memory.markdown_store import MarkdownMemoryStore


def test_backup_rejects_path_traversal_and_tampered_checksum(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    backup_mgr = VaultBackupManager(store)

    # Craft malicious tarball with .. traversal
    bad_tar = tmp_path / "bad.tar.gz"
    with tarfile.open(bad_tar, "w:gz") as tar:
        data = b"pwned"
        info = tarfile.TarInfo(name="../outside.txt")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))

    with pytest.raises(ValueError, match="Unsafe archive path"):
        backup_mgr.restore_backup(bad_tar)

    # Create valid backup, then tamper with manifest checksum
    m = store.remember("Valid note", "Original content.", scope=MemoryScope.GENERAL).record
    good_tar = tmp_path / "good.tar.gz"
    backup_mgr.create_backup(good_tar)

    tampered_tar = tmp_path / "tampered.tar.gz"
    with tarfile.open(good_tar, "r:gz") as src, tarfile.open(tampered_tar, "w:gz") as dst:
        for member in src.getmembers():
            raw = src.extractfile(member).read()  # type: ignore[union-attr]
            if member.name == m.relative_path:
                raw = b"tampered content"
            new_info = tarfile.TarInfo(name=member.name)
            new_info.size = len(raw)
            dst.addfile(new_info, io.BytesIO(raw))

    with pytest.raises(ValueError, match="Checksum mismatch"):
        backup_mgr.restore_backup(tampered_tar, overwrite=True)


def test_restore_overwrite_creates_pre_restore_snapshot(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    m = store.remember("Rollback test", "Version 1.", scope=MemoryScope.GENERAL).record
    backup_mgr = VaultBackupManager(store)

    snap_v1 = tmp_path / "v1.tar.gz"
    backup_mgr.create_backup(snap_v1)

    # Modify file on disk, then restore with overwrite=True
    mem_file = tmp_path / m.relative_path
    mem_file.write_text(mem_file.read_text(encoding="utf-8").replace("Version 1.", "Version 2."), encoding="utf-8")

    res = backup_mgr.restore_backup(snap_v1, overwrite=True)
    assert res["pre_restore_snapshot"] is not None
    assert Path(res["pre_restore_snapshot"]).exists()
    assert "Version 1." in mem_file.read_text(encoding="utf-8")


@pytest.mark.parametrize("template_name", VALID_TEMPLATES)
def test_starter_vault_templates_preserve_user_files(tmp_path: Path, template_name: str) -> None:
    vault = tmp_path / template_name
    assert cli_main(["--vault", str(vault), "init", "--template", template_name]) == 0
    assert (vault / "Home.md").exists()
    assert (vault / "AGENTS.md").exists()
    assert (vault / "vault-manifest.json").exists()

    # Customize Home.md and re-run template install -> must not overwrite
    (vault / "Home.md").write_text("# My Custom Home\n", encoding="utf-8")
    second = install_starter_template(vault, template_name)
    assert second["copied"] == 0
    assert second["skipped"] > 0
    assert (vault / "Home.md").read_text(encoding="utf-8") == "# My Custom Home\n"
