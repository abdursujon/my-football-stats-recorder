import subprocess
from pathlib import Path


class GitPublishingError(Exception):
    pass


def run_git_command(git_arguments, working_directory, run_command=subprocess.run):
    return run_command(
        ["git", *git_arguments],
        cwd=working_directory,
        capture_output=True,
        text=True,
        check=False,
    )


def find_git_repository_root_for_file(file_path, run_command=subprocess.run):
    completed_process = run_git_command(
        ["rev-parse", "--show-toplevel"], Path(file_path).resolve().parent, run_command
    )
    if completed_process.returncode != 0:
        return None
    return Path(completed_process.stdout.strip())


def commit_and_push_stats_readme(
    readme_file_path, commit_message, push_to_remote=True, run_command=subprocess.run
):
    repository_root = find_git_repository_root_for_file(readme_file_path, run_command)
    if repository_root is None:
        raise GitPublishingError(f"{readme_file_path} is not inside a git repository")

    readme_path_in_repository = str(
        Path(readme_file_path).resolve().relative_to(repository_root.resolve())
    )

    def run_git_and_raise_on_failure(git_arguments):
        completed_process = run_git_command(git_arguments, repository_root, run_command)
        if completed_process.returncode != 0:
            raise GitPublishingError(
                f"git {' '.join(git_arguments)} failed: {(completed_process.stderr or completed_process.stdout).strip()}"
            )
        return completed_process

    run_git_and_raise_on_failure(["add", "--", readme_path_in_repository])
    staged_difference = run_git_command(
        ["diff", "--cached", "--quiet", "--", readme_path_in_repository],
        repository_root,
        run_command,
    )
    if staged_difference.returncode == 0:
        return False

    run_git_and_raise_on_failure(
        ["commit", "-m", commit_message, "--", readme_path_in_repository]
    )
    if push_to_remote:
        run_git_and_raise_on_failure(["push"])
    return True
