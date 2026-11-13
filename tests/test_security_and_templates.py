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


def test_sensitive_secrets_redacted_before_persistence_on_disk(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    raw_api_key = "sk-12345678901234567890abcdef"
    raw_gh_token = "ghp_12345678901234567890abcdef"
    raw_google_key = "AIzaSyD12345678901234567890abcdef"
    
    result = store.remember(
        f"API credentials for {raw_api_key}",
        f"Here is the secret token: {raw_gh_token} and google: {raw_google_key}",
        scope=MemoryScope.GENERAL,
    )
    rec = result.record
    file_on_disk = tmp_path / rec.relative_path
    disk_content = file_on_disk.read_text(encoding="utf-8")

    # Secrets must be redacted BEFORE writing to disk
    assert raw_api_key not in disk_content
    assert raw_gh_token not in disk_content
    assert raw_google_key not in disk_content
    assert "[REDACTED_API_KEY]" in disk_content
    assert "[REDACTED_GITHUB_TOKEN]" in disk_content
    assert "[REDACTED_GOOGLE_KEY]" in disk_content


def test_sensitive_secrets_redacted_in_corrections_log(tmp_path: Path) -> None:
    store = MarkdownMemoryStore(tmp_path)
    res = store.remember("Original Note", "Initial body", scope=MemoryScope.GENERAL)
    rec = res.record

    raw_secret_in_reason = "sk-secretreason123456789012345"
    raw_secret_in_body = "sk-newsecretbody123456789012345"

    store.correct(
        rec.id,
        "Updated Title",
        f"Updated body containing {raw_secret_in_body}",
        reason=f"Correcting due to leaked key {raw_secret_in_reason}",
    )

    corrections_log_file = tmp_path / ".tm-brain" / "corrections.jsonl"
    log_content = corrections_log_file.read_text(encoding="utf-8")

    assert raw_secret_in_reason not in log_content
    assert "[REDACTED_API_KEY]" in log_content


def test_hermes_adapter_stores_redacted_episodes_and_kv(tmp_path: Path) -> None:
    from tm_second_brain.adapters.hermes import MainHermesAdapter
    store = MarkdownMemoryStore(tmp_path)
    adapter = MainHermesAdapter(store)

    raw_key = "sk-hermessecret123456789012345"
    adapter.store_episode("sess1", "agent1", {"title": "Test episode", "content": f"Secret: {raw_key}"})

    all_disk_files = list(tmp_path.rglob("*.md"))
    combined_text = "\n".join(f.read_text(encoding="utf-8") for f in all_disk_files)
    assert raw_key not in combined_text
    assert "[REDACTED_API_KEY]" in combined_text

