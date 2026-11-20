"""Exercise checkpoint guards against actual staged Git objects and hook processes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/check_handoff.py"
ZERO = "0" * 40


class GitFixture:
    def __init__(self, root):
        self.root = root
        self.env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
        for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            self.env.pop(name, None)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Checkpoint Tester")
        self.git("config", "user.email", "tester@example.com")
        self.write("app.py", "print('baseline')\n")
        self.write(
            "docs/handoff.md",
            "# Master handoff\n\n## Entries\n\n"
            "### 2026-11-13 — Legacy work\n\nHistorical record stays verbatim.\n",
        )
        self.git("add", ".")
        self.git("commit", "-m", "legacy baseline")
        self.baseline = self.head
        self.checkpoint("Activate checkpoints")
        self.git("commit", "-m", "activate checkpoint")

    @property
    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    @property
    def document(self):
        return (self.root / "docs/handoff.md").read_text()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def git(self, *args, check=True, input=None):
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            env=self.env,
            text=True,
            input=input,
            capture_output=True,
            check=check,
        )

    def guard(self, *args, check=True, input=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.root,
            env=self.env,
            text=True,
            input=input,
            capture_output=True,
            check=check,
        )

    def checkpoint(self, work, *, refresh=True):
        previous = self.document
        history = previous.split("## Entries\n", 1)[1].lstrip("\n")
        self.write(
            "docs/handoff.md",
            f"""# Master handoff

## Current state

- **Last worked on:** {work}
- **Stopping point:** This change is ready for review.
- **Highest priority:** E-04 navigation
- **Next pickup:** Implement bounded physical row navigation.
- **Verification:** Synthetic Git checks passed.

## Next up

1. E-04 navigation
   Reuse source verification before selection.
2. E-05 provenance

## Entries

### 2026-11-14 — {work}

- **Worked on:** {work}
- **Stopping point:** This change is ready for review.
- **Priorities:** E-04 navigation
- **Next pickup:** Implement bounded physical row navigation.
- **Verification:** Synthetic Git checks passed.

{history}""",
        )
        self.git("add", ".")
        if refresh:
            self.guard("--refresh")
            self.git("add", "docs/handoff.md")

    def install_hooks(self):
        for name in ("pre-commit", "pre-push"):
            target = self.root / ".githooks" / name
            target.parent.mkdir(exist_ok=True)
            shutil.copy(ROOT / ".githooks" / name, target)
            target.chmod(0o755)
        target = self.root / "scripts"
        target.mkdir(exist_ok=True)
        shutil.copy(SCRIPT, target / "check_handoff.py")
        shutil.copy(ROOT / "scripts/check_author.py", target / "check_author.py")
        self.write(
            ".author-policy.toml",
            'allowed_authors = [{name="Checkpoint Tester", '
            'email="tester@example.com"}]\nblocked_identity_patterns = ["robot"]\n',
        )
        self.git("config", "core.hooksPath", ".githooks")
        # Git invokes python3; use the test interpreter rather than a machine-specific default.
        bindir = self.root / "bin"
        bindir.mkdir()
        (bindir / "python3").symlink_to(sys.executable)
        self.env["PATH"] = str(bindir) + os.pathsep + self.env["PATH"]


class FilesystemFixture:
    """Run the filesystem checkpoint commands in a directory that is not a Git repository."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir()
        self.write("app.py", "print('baseline')\n")
        self.write("remove.txt", "remove me\n")
        self.write_master("Initial filesystem baseline")
        self.no_git_env = {**os.environ, "PATH": str(root / "no-git-on-path")}

    @property
    def document(self) -> str:
        return (self.root / "docs/handoff.md").read_text()

    @property
    def state_path(self) -> Path:
        return self.root / ".finassert-handoff/state.json"

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def write_master(self, work: str) -> None:
        if (self.root / "docs/handoff.md").exists():
            history = self.document.split("## Entries\n", 1)[1].lstrip("\n")
        else:
            history = ""
        self.write(
            "docs/handoff.md",
            f"""# Master handoff

## Current state

- **Last worked on:** {work}
- **Stopping point:** This filesystem change is ready for review.
- **Highest priority:** E-04 navigation
- **Next pickup:** Implement bounded physical row navigation.
- **Verification:** Filesystem guard checks passed.

## Next up

1. E-04 navigation
   Reuse source verification before selection.
2. E-05 provenance

## Entries

### 2026-11-19 — {work}

- **Worked on:** {work}
- **Stopping point:** This filesystem change is ready for review.
- **Priorities:** E-04 navigation
- **Next pickup:** Implement bounded physical row navigation.
- **Verification:** Filesystem guard checks passed.

{history}""",
        )

    def guard(self, *args: str, check: bool = True):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                *args,
                "--filesystem-root",
                str(self.root),
            ],
            cwd=self.root,
            env=self.no_git_env,
            text=True,
            capture_output=True,
            check=check,
        )


@pytest.fixture
def repo(tmp_path):
    return GitFixture(tmp_path)


@pytest.fixture
def filesystem(tmp_path):
    return FilesystemFixture(tmp_path / "filesystem-project")


def failure(result, fragment):
    assert result.returncode != 0
    assert fragment in result.stderr, result.stderr


def context(repo):
    return json.loads(repo.document.split("```json\n", 1)[1].split("\n```", 1)[0])


def test_refresh_uses_index_and_actual_git_context_without_staging(repo):
    repo.write("file with spaces.txt", "staged\n")
    repo.checkpoint("Implement feature", refresh=False)
    original_index = repo.git("show", ":docs/handoff.md").stdout
    repo.write("file with spaces.txt", "unstaged later edit\n")
    repo.guard("--refresh")
    assert repo.git("show", ":docs/handoff.md").stdout == original_index
    record = context(repo)
    assert record["prior_head"] == repo.head
    assert record["recent_commits"][0] == {"commit": repo.head, "subject": "activate checkpoint"}
    assert record["changed_paths"] == ["docs/handoff.md", "file with spaces.txt"]
    repo.git("add", "docs/handoff.md")
    repo.guard("--staged")
    repo.git("commit", "-m", "feature")
    repo.guard("--commit", "HEAD")
    assert repo.git("show", "HEAD:file with spaces.txt").stdout == "staged\n"


def test_unstaged_handoff_cannot_satisfy_staged_source_changes(repo):
    repo.write("app.py", "print('new')\n")
    repo.git("add", "app.py")
    repo.write("docs/handoff.md", repo.document + "\nAn unstaged note.\n")
    failure(repo.guard("--staged", check=False), "same commit")
    failure(repo.guard("--refresh", check=False), "Stage your master handoff prose first")


@pytest.mark.parametrize(
    "field", ["Last worked on", "Stopping point", "Highest priority", "Next pickup", "Verification"]
)
def test_required_current_fields_cannot_be_empty_placeholders(repo, field):
    repo.checkpoint("New work", refresh=False)
    lines = repo.document.splitlines()
    lines = [
        f"- **{field}:** TODO" if line.startswith(f"- **{field}:**") else line for line in lines
    ]
    repo.write("docs/handoff.md", "\n".join(lines) + "\n")
    repo.git("add", "docs/handoff.md")
    failure(repo.guard("--refresh", check=False), "placeholders")


@pytest.mark.parametrize(
    "mutation,fragment",
    [
        ("priority", "item 1"),
        ("pickup", "must match"),
        ("history", "verbatim"),
        ("missing_entry", "must match"),
        ("date", "valid ISO date"),
        ("duplicate", "Duplicate master section"),
    ],
)
def test_inconsistent_or_rewritten_master_is_rejected(repo, mutation, fragment):
    old = repo.document
    repo.checkpoint("New work", refresh=False)
    text = repo.document
    if mutation == "priority":
        text = text.replace("1. E-04 navigation", "1. A different priority")
    elif mutation == "pickup":
        text = text.replace("**Next pickup:** Implement", "**Next pickup:** Start", 1)
    elif mutation == "history":
        text = text.replace("Historical record stays verbatim.", "Rewritten history.")
    elif mutation == "missing_entry":
        text = text.split("## Entries\n", 1)[0] + "## Entries\n" + old.split("## Entries\n", 1)[1]
    elif mutation == "date":
        text = text.replace("### 2026-11-14 — New work", "### 2026-02-30 — New work")
    else:
        text += "\n## Next up\n\n1. Duplicate\n"
    repo.write("docs/handoff.md", text)
    repo.git("add", "docs/handoff.md")
    failure(repo.guard("--refresh", check=False), fragment)


def test_priority_reaffirmation_and_explicit_no_pickup_are_valid(repo):
    repo.checkpoint("Documentation repair", refresh=False)
    repo.write(
        "docs/handoff.md",
        repo.document.replace(
            "Implement bounded physical row navigation.",
            "No active pickup; select Next up item 1.",
            2,
        ),
    )
    repo.git("add", "docs/handoff.md")
    repo.guard("--refresh")
    repo.git("add", "docs/handoff.md")
    repo.guard("--staged")


@pytest.mark.parametrize(
    "mutation,fragment",
    [
        ("paths", "paths changed"),
        ("prose", "must match"),
        ("project", "snapshot changed"),
        ("recent", "Recent commit"),
    ],
)
def test_refresh_is_invalidated_by_later_staged_changes(repo, mutation, fragment):
    repo.checkpoint("New checkpoint")
    if mutation == "paths":
        repo.write("added.txt", "new\n")
        repo.git("add", "added.txt")
    elif mutation == "project":
        repo.write("app.py", "changed\n")
        repo.git("add", "app.py")
        repo.guard("--refresh")
        repo.git("add", "docs/handoff.md")
        repo.write("app.py", "changed again\n")
        repo.git("add", "app.py")
    else:
        text = repo.document
        text = (
            text.replace("**Worked on:** New checkpoint", "**Worked on:** Different work")
            if mutation == "prose"
            else text.replace('"subject": "activate checkpoint"', '"subject": "invented"')
        )
        repo.write("docs/handoff.md", text)
        repo.git("add", "docs/handoff.md")
    failure(repo.guard("--staged", check=False), fragment)


def test_renames_deletions_and_intent_to_add_respect_the_index(repo):
    repo.git("mv", "app.py", "renamed app.py")
    repo.checkpoint("Rename app")
    repo.write("not staged.txt", "later\n")
    repo.git("add", "--intent-to-add", "not staged.txt")
    repo.guard("--staged")
    assert context(repo)["changed_paths"] == ["app.py", "docs/handoff.md", "renamed app.py"]
    repo.git("commit", "-m", "rename")
    repo.guard("--commit", "HEAD")


def test_history_grandfathers_legacy_but_catches_bypassed_intermediate_work(repo):
    repo.guard("--history", "HEAD")
    repo.write("app.py", "bypassed\n")
    repo.git("add", "app.py")
    repo.git("commit", "-m", "bypassed hook")
    bad = repo.head
    repo.checkpoint("Recover checkpoint")
    repo.git("commit", "-m", "recovery")
    repo.guard("--commit", "HEAD")
    result = repo.guard("--range", repo.baseline, "HEAD", check=False)
    failure(result, bad[:12])
    failure(result, "same commit")


def test_checkpoint_activation_cannot_be_removed(repo):
    repo.write("docs/handoff.md", "# Removed checkpoint\n")
    repo.git("add", "docs/handoff.md")
    repo.git("commit", "-m", "remove policy without hooks")
    failure(repo.guard("--history", "HEAD", check=False), "no active master checkpoint")
    failure(repo.guard("--commit", "HEAD", check=False), "missing, removed or duplicated")


def test_empty_commits_do_not_require_fake_work(repo):
    repo.git("commit", "--allow-empty", "-m", "empty marker")
    repo.guard("--commit", "HEAD")
    repo.guard("--staged")


def test_new_remote_branch_checks_all_local_history(repo):
    repo.checkpoint("Valid next change")
    repo.git("commit", "-m", "next")
    repo.guard("--pre-push", input=f"refs/heads/work {repo.head} refs/heads/work {ZERO}\n")
    failure(repo.guard("--range", ZERO, repo.baseline, check=False), "no active master checkpoint")


def test_unknown_remote_history_requires_fetch_before_push(repo):
    failure(
        repo.guard(
            "--pre-push",
            check=False,
            input=(f"refs/heads/work {repo.head} refs/heads/work {'f' * 40}\n"),
        ),
        "Fetch the remote/base",
    )


def test_force_rewind_cannot_discard_a_newer_master_checkpoint(repo):
    old = repo.head
    repo.checkpoint("Newer checkpoint")
    repo.git("commit", "-m", "newer")
    failure(repo.guard("--range", repo.head, old, check=False), "drops remote/base")


def test_rewritten_history_can_preserve_remote_checkpoints(repo):
    published, document = repo.head, repo.document
    repo.git("switch", "-c", "rewrite", repo.baseline)
    repo.write("docs/handoff.md", document)
    repo.checkpoint("Preserve published work")
    repo.git("commit", "-m", "rewritten history with retained checkpoints")
    repo.guard("--range", published, "HEAD")


def test_multi_ref_push_checks_each_branch_and_ignores_tags_and_deletions(repo):
    good = repo.head
    repo.write("app.py", "bypassed\n")
    repo.git("add", "app.py")
    repo.git("commit", "-m", "bad branch")
    lines = (
        f"refs/tags/v0 {repo.baseline} refs/tags/v0 {ZERO}\n"
        f"(delete) {ZERO} refs/heads/old {good}\n"
        f"refs/heads/good {good} refs/heads/good {good}\n"
        f"refs/heads/bad {repo.head} refs/heads/bad {good}\n"
    )
    failure(repo.guard("--pre-push", input=lines, check=False), "same commit")


@pytest.mark.parametrize("mode", ["merge", "squash"])
def test_unchanged_project_checkpoint_survives_server_merge_or_squash(repo, mode):
    main = repo.head
    repo.git("switch", "-c", "feature")
    repo.write("app.py", "feature\n")
    repo.checkpoint("Feature work")
    repo.git("commit", "-m", "feature work")
    repo.git("switch", "main")
    if mode == "merge":
        repo.git("merge", "--no-ff", "feature", "-m", "Merge feature")
    else:
        repo.git("merge", "--squash", "feature")
        repo.git("commit", "-m", "Squash feature")
    repo.guard("--range", main, "HEAD")


def test_merge_with_new_unrecorded_project_content_fails(repo):
    main = repo.head
    repo.git("switch", "-c", "feature")
    repo.write("feature.txt", "feature\n")
    repo.checkpoint("Feature work")
    repo.git("commit", "-m", "feature")
    repo.git("switch", "main")
    repo.write("other.txt", "independent\n")
    repo.git("add", "other.txt")
    repo.git("commit", "-m", "bypassed independent change")
    repo.git("merge", "--no-ff", "feature", "-m", "Merge changed project")
    failure(repo.guard("--commit", "HEAD", check=False), "paths changed")
    failure(repo.guard("--range", main, "HEAD", check=False), "same commit")


def test_real_commit_and_push_hooks_preserve_author_and_block_stale_work(repo, tmp_path):
    repo.install_hooks()
    repo.write("app.py", "new work\n")
    repo.git("add", "app.py")
    failure(repo.git("commit", "-m", "stale", check=False), "same commit")
    repo.checkpoint("Install and exercise hooks")
    repo.git("config", "user.name", "robot")
    failure(repo.git("commit", "-m", "bad author", check=False), "Git author policy failed")
    repo.git("config", "user.name", "Checkpoint Tester")
    repo.git("commit", "-m", "valid checkpoint")
    remote = tmp_path / "remote.git"
    repo.git("init", "--bare", str(remote))
    repo.git("remote", "add", "origin", str(remote))
    repo.git("push", "-u", "origin", "main")
    repo.write("app.py", "bypassed\n")
    repo.git("add", "app.py")
    repo.git("-c", "core.hooksPath=/dev/null", "commit", "-m", "bypass local commit hook")
    failure(repo.git("push", "origin", "main", check=False), "same commit")


def test_refresh_cannot_reuse_context_after_new_head(repo):
    repo.checkpoint("Next work")
    repo.write(
        "docs/handoff.md",
        repo.document.replace(f'"prior_head": "{repo.head}"', f'"prior_head": "{repo.baseline}"'),
    )
    repo.git("add", "docs/handoff.md")
    failure(repo.guard("--staged", check=False), "predates HEAD")


def test_refresh_and_validation_work_from_a_subdirectory(repo):
    repo.checkpoint("Subdirectory work", refresh=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--refresh"],
        cwd=repo.root / "docs",
        env=repo.env,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    repo.git("add", "docs/handoff.md")
    repo.guard("--staged")


def test_root_checkpoint_without_a_parent_is_valid(repo):
    repo.git("checkout", "--orphan", "isolated")
    repo.git("rm", "-rf", ".")
    repo.write("docs/handoff.md", "# Master\n\n## Entries\n\n")
    repo.write("root.txt", "first project content\n")
    repo.checkpoint("Initial checkpoint")
    assert context(repo)["prior_head"] is None
    assert context(repo)["recent_commits"] == []
    repo.guard("--staged")
    repo.git("commit", "-m", "root checkpoint")
    repo.guard("--history", "HEAD")


def test_shallow_clone_is_rejected_with_recovery_instructions(repo):
    target = repo.root / "shallow-clone"
    repo.git("clone", "--depth=1", repo.root.as_uri(), str(target))
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--history", "HEAD"],
        cwd=target,
        env=repo.env,
        text=True,
        capture_output=True,
    )
    failure(result, "git fetch --unshallow")


def test_squash_retains_archived_git_context_after_source_objects_are_pruned(repo):
    repo.git("switch", "-c", "feature")
    repo.write("app.py", "first feature\n")
    repo.checkpoint("First feature checkpoint")
    repo.git("commit", "-m", "first feature")
    anchor = repo.head
    repo.write("app.py", "second feature\n")
    repo.checkpoint("Second feature checkpoint")
    repo.git("commit", "-m", "second feature")
    repo.git("switch", "main")
    repo.git("merge", "--squash", "feature")
    repo.git("commit", "-m", "squashed feature")
    repo.git("branch", "-D", "feature")
    repo.git("reflog", "expire", "--expire=now", "--all")
    repo.git("gc", "--prune=now")
    assert repo.git("cat-file", "-e", anchor, check=False).returncode != 0
    repo.guard("--commit", "HEAD")


def test_unresolved_index_conflicts_are_blocked(repo):
    repo.checkpoint("Conflict work", refresh=False)
    blob = repo.git("rev-parse", "HEAD:app.py").stdout.strip()
    repo.git(
        "update-index",
        "--index-info",
        input=(
            f"0 {ZERO}\tapp.py\n100644 {blob} 1\tapp.py\n100644 {blob} 2\tapp.py\n"
            f"100644 {blob} 3\tapp.py\n"
        ),
    )
    failure(repo.guard("--refresh", check=False), "index conflicts")


def test_boolean_is_not_a_checkpoint_schema_version(repo):
    repo.checkpoint("Version work")
    repo.write("docs/handoff.md", repo.document.replace('"version": 1', '"version": true'))
    repo.git("add", "docs/handoff.md")
    failure(repo.guard("--staged", check=False), "schema")


def filesystem_context(filesystem):
    return json.loads(filesystem.document.split("```json\n", 1)[1].split("\n```", 1)[0])


def test_filesystem_mode_initializes_and_checkpoints_without_git(filesystem):
    result = filesystem.guard("--filesystem-init")
    assert "initialized" in result.stdout
    initial = json.loads(filesystem.state_path.read_text())
    assert initial["mode"] == "filesystem"
    assert "prior_head" not in initial["baseline"]
    filesystem.guard("--filesystem-check")

    filesystem.write("app.py", "print('changed')\n")
    failure(filesystem.guard("--filesystem-check", check=False), "updated docs/handoff.md")
    filesystem.write_master("Track a filesystem-only change")
    state_before_refresh = filesystem.state_path.read_text()
    filesystem.guard("--filesystem-refresh-context")
    assert filesystem.state_path.read_text() == state_before_refresh
    context = filesystem_context(filesystem)
    assert context["mode"] == "filesystem"
    assert context["changed_paths"] == ["app.py", "docs/handoff.md"]
    filesystem.guard("--filesystem-check")
    filesystem.guard("--filesystem-checkpoint")
    accepted = json.loads(filesystem.state_path.read_text())
    assert accepted["baseline"]["checkpoint_id"] == context["checkpoint_id"]
    filesystem.guard("--filesystem-check")


def test_filesystem_mode_detects_added_deleted_and_renamed_files(filesystem):
    filesystem.write("src/old.py", "old\n")
    filesystem.guard("--filesystem-init")
    (filesystem.root / "src/old.py").rename(filesystem.root / "src/new.py")
    (filesystem.root / "remove.txt").unlink()
    filesystem.write("added.txt", "added\n")
    filesystem.write_master("Record filesystem rename and deletion")
    filesystem.guard("--filesystem-refresh-context")
    assert filesystem_context(filesystem)["changed_paths"] == [
        "added.txt",
        "docs/handoff.md",
        "remove.txt",
        "src/new.py",
        "src/old.py",
    ]


def test_filesystem_mode_uses_configured_rules_and_ignores_its_state(filesystem):
    filesystem.guard(
        "--filesystem-init",
        "--filesystem-include",
        "src/**",
        "--filesystem-include",
        "docs/**",
    )
    filesystem.write("dist/generated.txt", "ignored\n")
    filesystem.guard("--filesystem-check")
    filesystem.write("src/checked.py", "tracked\n")
    filesystem.write_master("Track configured source files")
    filesystem.guard("--filesystem-refresh-context")
    assert filesystem_context(filesystem)["changed_paths"] == [
        "docs/handoff.md",
        "src/checked.py",
    ]


def test_filesystem_mode_rejects_rewritten_history_and_stale_context(filesystem):
    filesystem.guard("--filesystem-init")
    filesystem.write("app.py", "print('first change')\n")
    filesystem.write_master("Create a checkpoint")
    filesystem.guard("--filesystem-refresh-context")
    state_before_stale_check = filesystem.state_path.read_text()
    filesystem.write("later.py", "changed after refresh\n")
    failure(filesystem.guard("--filesystem-check", check=False), "stale")
    failure(filesystem.guard("--filesystem-checkpoint", check=False), "stale")
    assert filesystem.state_path.read_text() == state_before_stale_check

    filesystem.write_master("Replace the stale checkpoint")
    rewritten = filesystem.document.replace("Initial filesystem baseline", "Rewritten history")
    filesystem.write("docs/handoff.md", rewritten)
    failure(filesystem.guard("--filesystem-refresh-context", check=False), "verbatim")


@pytest.mark.parametrize("damage", ["missing", "invalid"])
def test_filesystem_mode_requires_explicit_recovery_for_missing_or_damaged_state(
    filesystem, damage
):
    filesystem.guard("--filesystem-init")
    if damage == "missing":
        filesystem.state_path.unlink()
    else:
        filesystem.state_path.write_text("not json")
    failure(filesystem.guard("--filesystem-check", check=False), "damaged")
    failure(filesystem.guard("--filesystem-recover", check=False), "explicit")
    filesystem.guard("--filesystem-recover", "--confirm-filesystem-recovery")
    filesystem.guard("--filesystem-check")


def test_filesystem_check_is_read_only_and_checkpoint_requires_fresh_context(filesystem):
    filesystem.guard("--filesystem-init")
    state_before = filesystem.state_path.read_text()
    filesystem.guard("--filesystem-check")
    assert filesystem.state_path.read_text() == state_before
    failure(filesystem.guard("--filesystem-checkpoint", check=False), "No refreshed")
    assert filesystem.state_path.read_text() == state_before
