# Git Backup Notifier

Git Backup Notifier is a Python script designed to backup uncommitted and unpushed files from multiple Git repositories. The script ensures that only relevant files are backed up, excluding specified directories and applying size filters. Additionally, the script sends notifications about the backup status via email, Telegram, and local notifications.

# Why?
This was written when I realized that most of my local project files were not backed up and the cat ran over my unlocked 
keyboard. Nothing much happened, but it could have been bad and cost me hours or days to recover.

There are two main use cases
1. Regular Backup of uncommitted and unpushed files from multiple Git repositories.
2. Use of 2 computers that need some kind if synchronization via apple cloud, google drive, onedrive or similar.

For instance you have a desktop and a laptop and you want to work on the same project on both computers.
You can't commit sensitive files like passwords, API keys, etc. to the repository. Sending them via E-Mail get's 
old quickly, especially when you make changes to those files frequently.
You can use this script to backup the uncommitted and unpushed files from the desktop to the laptop and vice versa. 

You'll need to manually copy the files from the backup medium to the repository folder on the other computer 
but that's easier than having to remote access the other computer to get those files.

```venv, .git, __pycache__``` are excluded by default. You can add more exclusion patterns in the config file.

## Features

- Backup uncommitted and unpushed files from multiple Git repositories.
- Exclude specific directories and file patterns from the backup.
- Apply minimum and maximum file size filters.
- Log the backup process, including files copied, skipped, and any errors encountered.
- Send notifications about the backup status via email, Telegram, and local notifications.
- Configurable via TOML files with support for default and user-specific configurations.

## Installation

### Prerequisites

- Python 3.6 or higher
- Git
- Install required Python packages using `pip`:

```sh
pip install -r requirements.txt
```

## Requirements
- toml: For parsing TOML configuration files.
- requests: For sending notifications via Telegram.
- plyer: For sending local notifications on various operating systems.

## Configuration

### Default Configuration
The default configuration file is located at config/default.toml. It contains the general settings, backup settings, exclusion patterns, and notification settings.

```
[BackupSettings]
backup_root_path = "/default/backup/path"
min_file_size = 0
max_file_size = 999999999  # in bytes
delete_after_days = 9999

[Exclusions]
exclude_patterns = ["*.log", "*.tmp", "*.bak"]
exclude_dirs = ["venv", ".git", "__pycache__"]

[Repositories]
repo_paths = ["/path/to/repo1", "/path/to/repo2"]

[Notifications]
email = "default@example.com"
smtp_server = "smtp.example.com"
smtp_port = 587
smtp_user = "user@example.com"
smtp_password = "password"
telegram_token = "default-telegram-bot-token"
telegram_chat_id = "default-telegram-chat-id"

[GeneralSettings]
test_mode = true

```

### User Configuration
You can create a user-specific configuration file to overridonfig/user_config.toml:e the default settings. 
For example, create a file named user_config.toml in the config directory and add the following content:

```
[BackupSettings]
backup_root_path = "/user/specified/backup/path"
min_file_size = 100  # in bytes
max_file_size = 20971520  # in bytes (20 MB)

[Repositories]
repo_paths = ["/path/to/user/repo1", "/path/to/user/repo2"]

[Notifications]
email = "user@example.com"
telegram_token = "user-telegram-bot-token"
telegram_chat_id = "user-telegram-chat-id"
```

## Command Line Arguments
You can also specify paths and override configuration settings via command line arguments.
    
    ```
    python -m git_backup_notifier.backup --source /path/to/source --destination /path/to/destination
    ``` 
# Usage
1. Set Up Configuration: Ensure you have your default.toml and optional user_config.toml in the config directory.
2. Run the Script: Execute the script using the following command:
    
    ```python -m git_backup_notifier.backup```

You can also specify a user configuration file:
    ```python -m git_backup_notifier.backup --source /path/to/source --destination /path/to/destination```
3. Check Logs and Notifications: The script logs its activities to a log file in the backuplog directory under 
the specified backup root path. Notifications will be sent as configured.

# Development
## Running Tests
To run the tests, execute the following command:

```pytest tests/```

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

# License
[MIT License](https://choosealicense.com/licenses/mit/)
```
