import requests
import logging
import os

class TelegramBot:
    """
    Simple Telegram Bot for sending alerts.
    """

    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('CHAT_ID')
        self.logger = logging.getLogger('finbot.notifier')

        if not self.token or not self.chat_id:
            self.logger.warning("TELEGRAM_TOKEN or CHAT_ID not set. Telegram notifications disabled.")
            self.enabled = False
        else:
            self.enabled = True

    def send_alert(self, message: str):
        """
        Send an alert message via Telegram.

        Args:
            message: The message to send
        """
        if not self.enabled:
            self.logger.debug(f"Telegram disabled. Would send: {message}")
            return

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            self.logger.debug(f"Telegram alert sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
