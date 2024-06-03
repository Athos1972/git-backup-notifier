import smtplib
from email.mime.text import MIMEText
import requests
from plyer import notification
import subprocess
import sys


def send_email_notification(to_address, subject, body, smtp_config=None):
    if not smtp_config:
        print("No SMTP configuration provided.")
        return
    server = smtp_config.get('smtp_server', 'smtp.example.com')

    if not server:
        print("No SMTP server provided.")
        return

    port = smtp_config.get('smtp_port', 587)
    username = smtp_config.get('smtp_user', 'dummy-username')
    password = smtp_config.get('smtp_password', 'your-password')
    from_address = smtp_config.get('from_address', 'test@dummy.com')

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'your-email@example.com'
    msg['To'] = to_address

    try:
        with smtplib.SMTP(server, port=port) as server:
            server.login(user=username, password=password)
            server.sendmail(from_addr=from_address, to_addrs=[to_address], msg=msg.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_telegram_notification(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send Telegram message: {e}")


def send_local_notification(title, message):
    if sys.platform == 'win32':
        notification.notify(
            title=title,
            message=message,
            app_name='Backup Script'
        )
    elif sys.platform == 'darwin':
        send_macos_notification(title, message)
    elif sys.platform.startswith('linux'):
        send_linux_notification(title, message)
    else:
        print(f"Local notifications are not supported on this platform: {sys.platform}")


def send_macos_notification(title, message):
    try:
        subprocess.run(['osascript', '-e', f'display notification "{message}" with title "{title}"'])
    except Exception as e:
        print(f"Failed to send MacOS notification: {e}")


def send_linux_notification(title, message):
    try:
        subprocess.run(['notify-send', title, message])
    except Exception as e:
        print(f"Failed to send Linux notification: {e}")


def send_notification(title, message, config):
    send_local_notification(title, message)
    if 'email' in config['Notifications']:
        send_email_notification(to_address=config['Notifications']['email'],
                                subject=title,
                                body=message,
                                smtp_config=config['Notifications'])
    if 'telegram_token' in config['Notifications'] and 'telegram_chat_id' in config['Notifications']:
        send_telegram_notification(config['Notifications']['telegram_token'],
                                   config['Notifications']['telegram_chat_id'], message)
