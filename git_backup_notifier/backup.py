import sys
import os
import argparse
from pathlib import Path
from git_backup_notifier.utils import setup_logger, validate_paths, check_free_space, load_config, \
    get_uncommitted_files, get_unpushed_files, copy_files, delete_old_files
from git_backup_notifier.notifications import send_notification


def backup_uncommitted_files(config, source_path=None, destination_path=None):
    """
    Backup uncommitted files from multiple git repositories based on the configuration file.
    """
    backup_settings = config.get('BackupSettings', {})
    backup_root_path = destination_path if destination_path else backup_settings.get('backup_root_path',
                                                                                     '/default/backup/path')
    min_file_size = backup_settings.get('min_file_size', 0)
    max_file_size = backup_settings.get('max_file_size', 999_999_999)
    delete_after_days = backup_settings.get('delete_after_days', 9999)

    repo_paths = [source_path] if source_path else config.get('Repositories', {}).get('repo_paths', [])
    exclude_patterns = config.get('Exclusions', {}).get('exclude_patterns', [])
    exclude_dirs = config.get('Exclusions', {}).get('exclude_dirs', ['venv', '.git', '__pycache__'])
    test_mode = config.get('GeneralSettings', {}).get('test_mode', True)

    deleted = 0
    skipped = 0
    copied = 0

    try:
        validate_paths([backup_root_path] + repo_paths)
        check_free_space(backup_root_path, 10 * 1024 * 1024)  # Check if there is at least 10 MB of free space

        log_dir = Path(backup_root_path) / 'backuplog'
        logger = setup_logger(log_dir)

        for repo_path in repo_paths:
            repo_name = Path(repo_path).name
            repo_backup_path = Path(backup_root_path) / repo_name
            try:
                uncommitted_files = get_uncommitted_files(repo_path)
                unpushed_files = get_unpushed_files(repo_path)
                all_files = set(uncommitted_files) | set(unpushed_files)
                copied_here, skipped_here = copy_files(all_files, repo_path, repo_backup_path, exclude_patterns,
                                                       exclude_dirs, min_file_size, max_file_size, logger, test_mode)
                copied += copied_here
                skipped += skipped_here
            except RuntimeError as e:
                logger.error(e)

        delete_old_files(backup_root_path, repo_paths, delete_after_days, logger, test_mode)
        send_notification("Backup Completed", "The backup process has completed successfully.", config)
    except (FileNotFoundError, NotADirectoryError, OSError) as e:
        print(f"Error: {e}")
        send_notification("Backup Failed", f"The backup process failed: {e}", config)
        sys.exit(1)

    logger.info(f"Backup completed: {copied} files copied, {skipped} files skipped, {deleted} files deleted.")
    print(f"Backup completed: {copied} files copied, {skipped} files skipped, {deleted} files deleted.")


def main():
    parser = argparse.ArgumentParser(description="Backup uncommitted and unpushed files from Git repositories.")
    parser.add_argument('config_path', type=str, nargs='?', default=None, help='Path to the user configuration file.')
    parser.add_argument('--source', type=str, help='Override source path.')
    parser.add_argument('--destination', type=str, help='Override destination path.')

    args = parser.parse_args()

    config = load_config('config/default.toml', args.config_path)

    try:
        backup_uncommitted_files(config, source_path=args.source, destination_path=args.destination)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
