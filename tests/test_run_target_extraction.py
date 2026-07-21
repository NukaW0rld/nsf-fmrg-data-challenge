from pathlib import Path
import os
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

import run_target_extraction as runner


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def make_repository(base_dir):
    root = Path(base_dir) / "repository"
    (root / "src").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "data" / "raw").mkdir(parents=True)
    (root / "src" / "targets.py").write_text("# repository marker\n", encoding="utf-8")
    (root / "scripts" / "run_target_extraction.py").write_text(
        "# repository marker\n",
        encoding="utf-8",
    )
    (root / "data" / "raw" / "sample.bin").write_bytes(b"raw-data")
    return root


def require_no_published_or_staged_output(root):
    require(
        not (root / "processed_data" / "targets").exists(),
        "a failed run must never publish a mixed-generation targets directory (CR-02)",
    )
    processed_data = root / "processed_data"
    if processed_data.exists():
        leftover_staging = [
            entry for entry in processed_data.iterdir()
            if entry.name.startswith(".targets-staging-")
        ]
        require(not leftover_staging, "a failed run must discard its staging directory (CR-02)")


def clean_stub(project_root, raw_dir, targets_dir, qa_dir, track_id):
    require(raw_dir == (project_root / "data" / "raw").resolve(), "stub must receive canonical raw path")
    require(
        targets_dir.parent == (project_root / "processed_data").resolve()
        and targets_dir.name.startswith(".targets-staging-"),
        "stub must receive a fresh staging directory under processed_data (CR-02)",
    )
    require(qa_dir == (targets_dir / "qa").resolve(), "stub must receive canonical QA path")
    (targets_dir / f"stub_{track_id}.txt").write_text("allowed output\n", encoding="utf-8")
    return {
        "track_id": track_id,
        "laser_power_w": 400,
        "valid_count": 1,
        "median_width_mm": 1.0,
        "mean_width_mm": 1.0,
    }


def test_repository_root_rejection_is_read_only():
    real_raw_dir = REPO_ROOT / "data" / "raw"
    nested_output = real_raw_dir / "processed_data" / "targets"
    require(not nested_output.exists(), "test precondition: real raw tree must not contain nested output")

    try:
        runner.resolve_repository_root(real_raw_dir, repository_anchor=REPO_ROOT)
    except ValueError as exc:
        require("repository" in str(exc).lower(), "root rejection must identify the repository mismatch")
    else:
        raise AssertionError("Expected the real data/raw directory to be rejected as project_dir")

    require(not nested_output.exists(), "root rejection must not create output under the real raw tree")


def test_symlink_output_into_raw_is_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)
        raw_dir = runner.resolve_raw_dir(root.resolve())
        before = runner.snapshot_raw(raw_dir)
        (root / "processed_data").symlink_to(raw_dir, target_is_directory=True)

        try:
            runner.run_pipeline(root, track_ids=(8,), track_runner=clean_stub, repository_anchor=root)
        except ValueError as exc:
            require("symlink" in str(exc).lower(), "symlink rejection must identify the offending symlinked path")
        else:
            raise AssertionError("Expected processed_data symlink traversal into raw to be rejected")

        require(before == runner.snapshot_raw(raw_dir), "symlink rejection must leave raw bytes and metadata unchanged")
        require(not (raw_dir / "targets" / "extraction_params.json").exists(), "parameter output must not appear through the symlink")


def test_symlink_at_backup_path_is_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)
        raw_dir = runner.resolve_raw_dir(root.resolve())
        before = runner.snapshot_raw(raw_dir)

        victim = root / "VICTIM"
        victim.mkdir()
        sentinel = victim / "sentinel.txt"
        sentinel.write_text("do not delete\n", encoding="utf-8")

        (root / "processed_data").mkdir()
        (root / "processed_data" / "targets.previous").symlink_to(victim, target_is_directory=True)

        try:
            runner.run_pipeline(root, track_ids=(8,), track_runner=clean_stub, repository_anchor=root)
        except ValueError as exc:
            require("symlink" in str(exc).lower(), "backup-path rejection must identify the symlinked path")
        else:
            raise AssertionError("Expected a symlinked targets.previous to be rejected")

        require(before == runner.snapshot_raw(raw_dir), "symlink rejection must leave raw bytes and metadata unchanged")
        require(
            sentinel.is_file() and sentinel.read_text(encoding="utf-8") == "do not delete\n",
            "victim directory and sentinel must survive a rejected publish",
        )
        require(
            not (root / "processed_data" / "targets").exists(),
            "targets must not be published when the backup path is a rejected symlink",
        )


def test_symlink_at_processed_data_is_rejected():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)
        raw_dir = runner.resolve_raw_dir(root.resolve())
        before = runner.snapshot_raw(raw_dir)

        victim = root / "VICTIM"
        victim.mkdir()
        sentinel = victim / "sentinel.txt"
        sentinel.write_text("do not delete\n", encoding="utf-8")

        (root / "processed_data").symlink_to(victim, target_is_directory=True)

        try:
            runner.run_pipeline(root, track_ids=(8,), track_runner=clean_stub, repository_anchor=root)
        except ValueError as exc:
            require("symlink" in str(exc).lower(), "processed_data rejection must identify the symlinked path")
        else:
            raise AssertionError("Expected a symlinked processed_data to be rejected")

        require(before == runner.snapshot_raw(raw_dir), "symlink rejection must leave raw bytes and metadata unchanged")
        require(
            sentinel.is_file() and sentinel.read_text(encoding="utf-8") == "do not delete\n",
            "victim directory and sentinel must survive a rejected publish",
        )
        require(
            not (victim / "targets").exists(),
            "targets must not be published through a symlinked processed_data path",
        )


def test_publish_refuses_symlinked_backup_immediately_before_rmtree():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)
        raw_dir = runner.resolve_raw_dir(root.resolve())
        project_root = root.resolve()

        victim = project_root / "VICTIM"
        victim.mkdir()
        sentinel = victim / "sentinel.txt"
        sentinel.write_text("do not delete\n", encoding="utf-8")

        processed_data = project_root / "processed_data"
        processed_data.mkdir()
        targets_dir = processed_data / "targets"
        targets_dir.mkdir()
        (targets_dir / "existing.txt").write_text("prior generation\n", encoding="utf-8")

        staging_dir = processed_data / ".targets-staging-test"
        staging_dir.mkdir()
        (staging_dir / "new.txt").write_text("new generation\n", encoding="utf-8")

        backup_dir = processed_data / "targets.previous"
        backup_dir.symlink_to(victim, target_is_directory=True)

        try:
            runner.publish_staging_dir(staging_dir, targets_dir, project_root, raw_dir)
        except ValueError as exc:
            require("symlink" in str(exc).lower(), "publish rejection must identify the symlinked backup path")
        else:
            raise AssertionError("Expected publish_staging_dir to reject a symlinked backup path")

        require(
            sentinel.is_file() and sentinel.read_text(encoding="utf-8") == "do not delete\n",
            "victim directory and sentinel must survive publish rejection",
        )
        require((targets_dir / "existing.txt").is_file(), "prior targets generation must remain untouched")


def test_snapshot_diff_classifies_add_remove_and_same_size_change():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)
        raw_dir = runner.resolve_raw_dir(root.resolve())
        sample = raw_dir / "sample.bin"

        before_add = runner.snapshot_raw(raw_dir)
        (raw_dir / "added.bin").write_bytes(b"added")
        after_add = runner.snapshot_raw(raw_dir)
        require(runner.raw_snapshot_diff(before_add, after_add) == {
            "added": ["added.bin"],
            "removed": [],
            "changed": [],
        }, "added files must be classified deterministically")

        before_remove = after_add
        (raw_dir / "added.bin").unlink()
        after_remove = runner.snapshot_raw(raw_dir)
        require(runner.raw_snapshot_diff(before_remove, after_remove) == {
            "added": [],
            "removed": ["added.bin"],
            "changed": [],
        }, "removed files must be classified deterministically")

        before_change = runner.snapshot_raw(raw_dir)
        original_stat = sample.stat()
        sample.write_bytes(b"RAW-DATA")
        os.utime(sample, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))
        after_change = runner.snapshot_raw(raw_dir)
        require(runner.raw_snapshot_diff(before_change, after_change) == {
            "added": [],
            "removed": [],
            "changed": ["sample.bin"],
        }, "same-size content changes must be detected by digest")


def test_success_path_audits_raw_in_finally():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)
        original_snapshot = runner.snapshot_raw
        calls = []

        def counting_snapshot(raw_dir):
            calls.append(raw_dir)
            return original_snapshot(raw_dir)

        runner.snapshot_raw = counting_snapshot
        try:
            summaries = runner.run_pipeline(
                root,
                track_ids=(8,),
                track_runner=clean_stub,
                repository_anchor=root,
            )
        finally:
            runner.snapshot_raw = original_snapshot

        require(summaries == [{
            "track_id": 8,
            "laser_power_w": 400,
            "valid_count": 1,
            "median_width_mm": 1.0,
            "mean_width_mm": 1.0,
        }], "successful pipeline must return track summaries")
        require(len(calls) == 2, "successful pipeline must take before and finally snapshots")
        require((root / "processed_data" / "targets" / "stub_8.txt").is_file(), "allowed output must be published below targets")
        leftover_staging = [
            entry for entry in (root / "processed_data").iterdir()
            if entry.name.startswith(".targets-staging-")
        ]
        require(not leftover_staging, "a successful publish must not leave a staging directory behind (CR-02)")


def test_injected_failure_propagates_after_clean_audit():
    class SentinelError(RuntimeError):
        pass

    sentinel = SentinelError("injected track failure")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)
        original_snapshot = runner.snapshot_raw
        calls = []

        def counting_snapshot(raw_dir):
            calls.append(raw_dir)
            return original_snapshot(raw_dir)

        def failing_stub(project_root, raw_dir, targets_dir, qa_dir, track_id):
            raise sentinel

        runner.snapshot_raw = counting_snapshot
        try:
            try:
                runner.run_pipeline(root, track_ids=(8,), track_runner=failing_stub, repository_anchor=root)
            except SentinelError as exc:
                require(exc is sentinel, "clean audit must preserve the original sentinel object")
            else:
                raise AssertionError("Expected the injected failure to propagate")
        finally:
            runner.snapshot_raw = original_snapshot

        require(len(calls) == 2, "failed pipeline must still take the finally snapshot")
        require_no_published_or_staged_output(root)


def test_raw_mutation_takes_precedence_and_chains_failure():
    sentinel = RuntimeError("injected failure after mutation")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)

        def mutating_stub(project_root, raw_dir, targets_dir, qa_dir, track_id):
            (raw_dir / "sample.bin").write_bytes(b"tampered")
            raise sentinel

        try:
            runner.run_pipeline(root, track_ids=(8,), track_runner=mutating_stub, repository_anchor=root)
        except RuntimeError as exc:
            require(exc is not sentinel, "integrity failure must take precedence over the pipeline error")
            require("changed" in str(exc).lower(), "integrity failure must name the changed category")
            require("sample.bin" in str(exc), "integrity failure must name the changed raw path")
            require(exc.__cause__ is sentinel, "integrity failure must chain the original pipeline error")
        else:
            raise AssertionError("Expected raw mutation to fail closed")

        require_no_published_or_staged_output(root)


def test_final_audit_failure_fails_closed():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = make_repository(temp_dir)
        original_snapshot = runner.snapshot_raw
        calls = 0

        def unavailable_final_snapshot(raw_dir):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected audit failure")
            return original_snapshot(raw_dir)

        runner.snapshot_raw = unavailable_final_snapshot
        try:
            try:
                runner.run_pipeline(root, track_ids=(8,), track_runner=clean_stub, repository_anchor=root)
            except RuntimeError as exc:
                require("audit" in str(exc).lower(), "unavailable final snapshot must raise an audit error")
                require(isinstance(exc.__cause__, OSError), "audit error must chain the snapshot failure")
            else:
                raise AssertionError("Expected unavailable final snapshot to fail closed")
        finally:
            runner.snapshot_raw = original_snapshot

        require_no_published_or_staged_output(root)


if __name__ == "__main__":
    tests = [
        test_repository_root_rejection_is_read_only,
        test_symlink_output_into_raw_is_rejected,
        test_symlink_at_backup_path_is_rejected,
        test_symlink_at_processed_data_is_rejected,
        test_publish_refuses_symlinked_backup_immediately_before_rmtree,
        test_snapshot_diff_classifies_add_remove_and_same_size_change,
        test_success_path_audits_raw_in_finally,
        test_injected_failure_propagates_after_clean_audit,
        test_raw_mutation_takes_precedence_and_chains_failure,
        test_final_audit_failure_fails_closed,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
