import subprocess

import pytest

from footie.publishing.git_publisher import (
    GitPublishingError,
    commit_and_push_stats_readme,
    find_git_repository_root_for_file,
)


def run_git_in_directory(working_directory, *git_arguments):
    return subprocess.run(
        ["git", *git_arguments],
        cwd=working_directory,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


@pytest.fixture
def stats_repository_with_remote(tmp_path):
    remote_directory = tmp_path / "remote.git"
    stats_repository = tmp_path / "stats"
    subprocess.run(["git", "init", "--bare", "-q", str(remote_directory)], check=True)
    subprocess.run(
        ["git", "clone", "-q", str(remote_directory), str(stats_repository)],
        check=True,
        capture_output=True,
    )
    run_git_in_directory(stats_repository, "config", "user.email", "player@example.com")
    run_git_in_directory(stats_repository, "config", "user.name", "Player")
    (stats_repository / "README.md").write_text("# Stats\n")
    (stats_repository / "notes.txt").write_text("draft\n")
    run_git_in_directory(stats_repository, "add", "README.md")
    run_git_in_directory(stats_repository, "commit", "-q", "-m", "Initial")
    run_git_in_directory(stats_repository, "push", "-q", "-u", "origin", "HEAD")
    return stats_repository, remote_directory


def test_changed_readme_is_committed_and_pushed_alone(stats_repository_with_remote):
    stats_repository, remote_directory = stats_repository_with_remote
    (stats_repository / "README.md").write_text("# Stats\nnew row\n")
    run_git_in_directory(stats_repository, "add", "notes.txt")

    assert commit_and_push_stats_readme(
        stats_repository / "README.md", "Record match stats"
    )

    assert (
        run_git_in_directory(remote_directory, "log", "-1", "--format=%s").strip()
        == "Record match stats"
    )
    committed_files = run_git_in_directory(
        stats_repository, "show", "--name-only", "--format=", "HEAD"
    ).split()
    assert committed_files == ["README.md"]
    assert "notes.txt" in run_git_in_directory(
        stats_repository, "diff", "--cached", "--name-only"
    )


def test_unchanged_readme_makes_no_commit(stats_repository_with_remote):
    stats_repository, _ = stats_repository_with_remote
    assert not commit_and_push_stats_readme(
        stats_repository / "README.md", "Nothing changed"
    )


def test_commit_without_push_leaves_remote_untouched(stats_repository_with_remote):
    stats_repository, remote_directory = stats_repository_with_remote
    (stats_repository / "README.md").write_text("# Stats\nlocal only\n")
    assert commit_and_push_stats_readme(
        stats_repository / "README.md", "Local commit", push_to_remote=False
    )
    assert (
        run_git_in_directory(remote_directory, "log", "-1", "--format=%s").strip()
        == "Initial"
    )


def test_readme_outside_git_repository_raises(tmp_path):
    readme_file_path = tmp_path / "README.md"
    readme_file_path.write_text("# Stats\n")
    assert find_git_repository_root_for_file(readme_file_path) is None
    with pytest.raises(GitPublishingError):
        commit_and_push_stats_readme(readme_file_path, "Record match stats")
