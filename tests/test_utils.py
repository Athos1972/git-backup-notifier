import tempfile
import shutil
from pathlib import Path
import subprocess
import pytest
from git_backup_notifier.utils import compute_file_hash, get_uncommitted_files, get_unpushed_files


@pytest.fixture(scope='module')
def setup_repo():
    temp_dir = tempfile.mkdtemp()
    try:
        fixture_dir = Path.cwd().joinpath('tests/fixtures') / 'repo1'
    except FileNotFoundError:
        fixture_dir = Path(__file__).parent.joinpath('fixtures') / 'repo1'
    dst = Path(temp_dir) / 'repo1'
    shutil.copytree(fixture_dir, dst)

    # Initialize Git and commit a single file
    subprocess.run(['git', 'init'], cwd=dst)
    subprocess.run(['git', 'add', 'file1.txt'], cwd=dst)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=dst)

    # This file is comitted but not pushed and show should up in unpushed files
    subprocess.run(['git', 'add', 'file_to_commit_but_not_push.txt'], cwd=dst)

    yield temp_dir, dst

    # Teardown
    shutil.rmtree(temp_dir)


def test_compute_file_hash(setup_repo):
    temp_dir, repo_path = setup_repo
    path = repo_path / 'file1.txt'
    hash1 = compute_file_hash(path)
    hash2 = compute_file_hash(path)
    assert hash1 == hash2


def test_get_uncommitted_files(setup_repo):
    temp_dir, repo_path = setup_repo
    files = get_uncommitted_files(repo_path)
    print(f"Uncommitted files: {files}")
    assert 'file2.txt' in files
    assert 'subdir/file3.txt' in files


def test_get_unpushed_files(setup_repo):
    temp_dir, repo_path = setup_repo
    files = get_unpushed_files(repo_path)
    print(f"Unpushed files: {files}")
    assert 'file1.txt' in files


if __name__ == '__main__':
    pytest.main([__file__])
