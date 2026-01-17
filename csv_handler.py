import csv
import os
from typing import Dict, Optional


class CSVHandler:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._users_cache = {}
        self._load_users()

    def _load_users(self):
        """Load users from CSV file into memory."""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        self._users_cache = {}
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                telegram_username = row.get('telegram_username', '').strip()
                email = row.get('email', '').strip()
                if telegram_username and email:
                    self._users_cache[telegram_username] = email

    def reload_users(self):
        """Reload users from CSV file."""
        self._load_users()

    def is_authorized(self, telegram_username: str) -> bool:
        """Check if a Telegram username is authorized."""
        if not telegram_username.startswith('@'):
            telegram_username = f'@{telegram_username}'
        self.reload_users()
        return telegram_username in self._users_cache

    def get_email(self, telegram_username: str) -> Optional[str]:
        """Get email for a given Telegram username."""
        if not telegram_username.startswith('@'):
            telegram_username = f'@{telegram_username}'
        self.reload_users()
        return self._users_cache.get(telegram_username)

    def get_all_users(self) -> Dict[str, str]:
        self.reload_users()
        """Get all authorized users."""
        return self._users_cache.copy()
