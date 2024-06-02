import smtplib
from email.mime.text import MIMEText
import requests
from plyer import notification
import subprocess
import sys


def send_email_notification(to_address, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'your-email@example.com'
    msg['To'] = to_address

    try:
        with smtplib.SMTP('smtp.example.com') as server:
            server.login('your-username', 'your-password')
            server.sendmail('your-email@example.com', [to_address], msg.as_string())
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
        send_email_notification(config['Notifications']['email'], title, message)
    if 'telegram_token' in config['Notifications'] and 'telegram_chat_id' in config['Notifications']:
        send_telegram_notification(config['Notifications']['telegram_token'], config['Notifications']['telegram_chat_id'], message)
