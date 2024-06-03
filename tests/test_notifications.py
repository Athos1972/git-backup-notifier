from git_backup_notifier.notifications import send_local_notification, send_email_notification, send_telegram_notification


def test_send_local_notification():
    send_local_notification("Test Notification", "This is a test message.")


def test_send_email_notification():
    smtp_config = {
        'smtp_user': 'user@example.com',
        'smtp_password': 'password',
        'smtp_server': 'smtp.example.com',
        'smtp_port': 587
    }
    send_email_notification("test@example.com", "Test Email", "This is a test email message.", smtp_config)


def test_send_telegram_notification():
    send_telegram_notification("test-telegram-bot-token", "test-telegram-chat-id", "This is a test Telegram message.")


if __name__ == '__main__':
    test_send_local_notification()
    test_send_email_notification()
    test_send_telegram_notification()
