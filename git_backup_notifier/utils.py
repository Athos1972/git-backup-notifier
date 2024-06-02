import os
import shutil
import subprocess
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import toml
import fnmatch


def setup_logger(log_dir):
    """
    Set up the logger for backup operations.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'backup.log'

    logger = logging.getLogger('backup_logger')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def load_config(default_path, user_path=None):
    """
    Load the default configuration and optionally merge it with a user-specified configuration.
    """
    config = toml.load(default_path)

    if user_path and Path(user_path).exists():
        user_config = toml.load(user_path)
        merge_dicts(config, user_config)

    return config


def merge_dicts(base, updates):
    """
    Recursively merge two dictionaries.
    """
    for key, value in updates.items():
        if isinstance(value, dict) and key in base:
            merge_dicts(base[key], value)
        else:
            base[key] = value


def get_uncommitted_files(repo_path):
    """
    Get a list of uncommitted files in a git repository.
    """
    try:
        os.chdir(repo_path)
        # Get untracked and ignored files
        result_untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], capture_output=True,
                                          text=True)
        result_ignored = subprocess.run(['git', 'ls-files', '--others', '--ignored', '--exclude-standard', '-o'],
                                        capture_output=True, text=True)

        untracked_files = result_untracked.stdout.splitlines()
        ignored_files = result_ignored.stdout.splitlines()

        # Get modified files
        result_modified = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        modified_files = [line[3:] for line in result_modified.stdout.splitlines() if line.startswith(' M')]

        # Combine all files
        files = untracked_files + ignored_files + modified_files

        # Expand directories to list all untracked files
        all_files = []
        for file in files:
            path = Path(file)
            if path.is_file():
                all_files.append(file)
            elif path.is_dir():
                for sub_file in path.rglob('*'):
                    if sub_file.is_file():
                        all_files.append(str(sub_file))
        return all_files
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get uncommitted files in {repo_path}: {e}")


def get_unpushed_files(repo_path):
    """
    Get a list of unpushed files in a git repository.
    """
    try:
        os.chdir(repo_path)
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip().decode()
        remote_branch = f'origin/{branch}'
        result = subprocess.run(['git', 'log', f'{remote_branch}..{branch}', '--name-only', '--pretty=format:'],
                                capture_output=True, text=True)
        files = set(result.stdout.splitlines())
        files.discard('')  # Remove empty strings
        # Expand directories to list all untracked files
        all_files = []
        for file in files:
            path = Path(file)
            if path.is_file():
                all_files.append(file)
            elif path.is_dir():
                for sub_file in path.rglob('*'):
                    if sub_file.is_file():
                        all_files.append(str(sub_file))
        return list(all_files)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get unpushed files in {repo_path}: {e}")


def compute_file_hash(file_path):
    """
    Compute the hash of a file.
    """
    hash_func = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def copy_files(file_list, src_base_path, dst_base_path, exclude_patterns, exclude_dirs, min_size, max_size, logger,
               test_mode=True):
    """
    Copy files from the source base path to the destination base path
    maintaining the directory structure and applying exclusions and size filters.
    """
    copied = 0
    skipped = 0
    for file in file_list:
        src_file = Path(src_base_path) / file

        # Skip files in excluded directories
        if any(excluded in src_file.parts for excluded in exclude_dirs):
            logger.debug(f"Skipped {src_file} (excluded by directory)")
            skipped += 1
            continue

        if any(fnmatch.fnmatch(src_file.name, pattern) for pattern in exclude_patterns):
            logger.debug(f"Skipped {src_file} (excluded by pattern)")
            skipped += 1
            continue
        if not (min_size <= src_file.stat().st_size <= max_size):
            logger.debug(f"Skipped {src_file} (file size out of range)")
            skipped += 1
            continue

        dst_file = Path(dst_base_path) / file
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            if dst_file.exists():
                src_mtime = src_file.stat().st_mtime
                dst_mtime = dst_file.stat().st_mtime
                src_size = src_file.stat().st_size
                dst_size = dst_file.stat().st_size

                # Check file size and modification time first
                if src_size == dst_size and src_mtime == dst_mtime:
                    skipped += 1
                    logger.debug(f"Skipped {src_file} (destination file is up to date based on size and mtime)")
                    continue
                else:
                    # Compute hash if size or mtime indicate a potential change
                    src_hash = compute_file_hash(src_file)
                    dst_hash = compute_file_hash(dst_file)
                    if src_hash == dst_hash:
                        skipped += 1
                        logger.debug(f"Skipped {src_file} (destination file is up to date based on hash)")
                        continue
                    else:
                        copied += 1
                        logger.info(f"Overwritten {dst_file} due to different hash value")
            else:
                copied += 1
                logger.info(f"Copied {src_file} to {dst_file}")

            if not test_mode:
                shutil.copy2(src_file, dst_file)
        except OSError as e:
            skipped += 1
            logger.error(f"Failed to copy {src_file} to {dst_file}: {e}")

    return copied, skipped


def delete_old_files(backup_root_path, repo_paths, delete_after_days, logger, test_mode=True):
    """
    Delete files from the backup that do not exist in the source repository
    if they are older than the specified number of days.
    """
    cutoff_date = datetime.now() - timedelta(days=delete_after_days)
    deleted = 0
    for repo_path in repo_paths:
        repo_name = Path(repo_path).name
        backup_path = Path(backup_root_path) / repo_name
        for root, _, files in os.walk(backup_path):
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(backup_path)
                src_file_path = Path(repo_path) / relative_path

                try:
                    if not src_file_path.exists() and datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:
                        if not test_mode:
                            file_path.unlink()
                        logger.info(
                            f"Deleted {file_path} (no longer in source and older than {delete_after_days} days)."
                            f"Test mode: {test_mode}")
                        deleted += 1
                except OSError as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

    return deleted


def validate_paths(paths):
    for path in paths:
        if not Path(path).exists():
            raise FileNotFoundError(f"Path not found: {path}")
        if not Path(path).is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")


def check_free_space(path, required_space):
    statvfs = os.statvfs(path)
    free_space = statvfs.f_frsize * statvfs.f_bavail
    if free_space < required_space:
        raise OSError(f"Not enough free space on device: {path}. Required: {required_space}, Available: {free_space}")
