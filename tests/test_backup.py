import os
import shutil
import tempfile
from pathlib import Path
import subprocess
import pytest
from git_backup_notifier.backup import backup_uncommitted_files
from git_backup_notifier.utils import load_config


@pytest.fixture(scope='module')
def setup_test_environment():
    temp_dir = tempfile.mkdtemp()
    fixture_dir = Path.cwd().joinpath('tests/fixtures')
    test_dirs = []

    # Setup the backup destination folder within the temporary directory
    Path(temp_dir).joinpath('backup').mkdir(exist_ok=True)

    for repo in ['repo1', 'repo2']:
        src = fixture_dir / repo
        dst = Path(temp_dir) / repo
        shutil.copytree(src, dst)

        # To make sure we can commit the files we needed to rename the .env file and the venv-Folder in the fixtures.
        # Otherwise .gitignore would have filtered them out. Now we must rename them back.
        if (dst / 'env').exists():
            (dst / 'env').rename(dst / '.env')

        if (dst / 'venv_trick').exists():
            (dst / 'venv_trick').rename(dst / 'venv')

        test_dirs.append(dst)

        # Initialize Git and commit a single file
        subprocess.run(['git', 'init'], cwd=dst)
        subprocess.run(['git', 'add', 'file1.txt' if repo == 'repo1' else 'file4.txt'], cwd=dst)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=dst)

    yield temp_dir, test_dirs

    # Teardown
    shutil.rmtree(temp_dir)


def touch_file(path):
    with open(path, 'a'):
        os.utime(path, None)


def test_backup(setup_test_environment):
    temp_dir, test_dirs = setup_test_environment

    config = load_config('config/default.toml', 'config/test_config.toml')
    config['BackupSettings']['backup_root_path'] = str(Path(temp_dir) / 'backup')
    config['Repositories']['repo_paths'] = [str(dir) for dir in test_dirs]

    touch_file(test_dirs[0] / 'file2.txt')
    touch_file(test_dirs[0] / 'subdir' / 'file3.txt')
    touch_file(test_dirs[1] / 'file4.txt')

    try:
        backup_uncommitted_files(config)
    except SystemExit:
        pass

    backup_path = Path(config['BackupSettings']['backup_root_path'])
    print(f"Checking backup at: {backup_path}")
    print(f"Contents of backup directory: {list(backup_path.rglob('*'))}")

    errors = []
    if not (backup_path / 'repo1' / 'file2.txt').exists():
        errors.append(f"{backup_path / 'repo1' / 'file2.txt'} does not exist.")
    if not (backup_path / 'repo1' / 'subdir' / 'file3.txt').exists():
        errors.append(f"{backup_path / 'repo1' / 'subdir' / 'file3.txt'} does not exist.")
    if not (backup_path / 'repo1' / '.env').exists():
        errors.append(f"{backup_path / 'repo1' / '.env'} should exist.")

    # Excluded as within venv-Folder. venv-Folder excluded in the config.
    if (backup_path / 'repo2' / 'venv' / 'dummy_file.txt').exists():
        errors.append(f"{backup_path / 'repo2' / 'venv' / 'dummy_file.txt'} should not exist.")

    # Has been touched - must be moved:
    if not (backup_path / 'repo2' / 'file4.txt').exists():
        errors.append(f"{backup_path / 'repo2' / 'file4.txt'} doesn't exist in destination.")

    assert not errors, "Errors occurred:\n{}".format("\n".join(errors))


if __name__ == '__main__':
    pytest.main([__file__])
