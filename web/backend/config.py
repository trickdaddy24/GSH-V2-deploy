import os
from dotenv import load_dotenv

load_dotenv()

DATE_FORMAT = "%m-%d-%Y"
DATE_INPUT_FORMATS = ("%m-%d-%y", "%m-%d-%Y", "%Y-%m-%d")
ACCOUNT_PREFIX = "dtv."
ACCOUNT_PADDING = 3
DELINQUENT_DAYS = 30
INITIAL_DAYS = 5
PAID_DAYS = 21
RISK_IMMINENT_DAYS = 4
RISK_GENERAL_MIN = 4
RISK_ENHANCED_MIN = 5
RISK_HIGH = 7
RISK_MAX_LATE = 3
MAX_PAYMENT_HISTORY = 5

CONFIG = {
    "PACKAGES": {
        "0": ("OnDemand", 10),
        "1": ("Grandfather", 25),
        "2": ("Silver", 30),
        "3": ("Gold", 40),
        "4": ("Platinum", 50),
        "5": ("Custom", None),
    },
    "DB_NAME": os.getenv("DB_PATH", "../../OnDemand_subscriptions.db"),
    "NOTIFICATIONS": {
        "EMAIL": {
            "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            "smtp_server": os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
            "username": os.getenv("EMAIL_USERNAME"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "from_email": os.getenv("EMAIL_FROM", "billing@guardianstreams.com"),
            "from_name": os.getenv("EMAIL_FROM_NAME", "GuardianStreams Billing"),
        },
        "TELEGRAM": {
            "enabled": os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
            "webhook_secret": os.getenv("TELEGRAM_WEBHOOK_SECRET", ""),
        },
        "DISCORD": {
            "enabled": os.getenv("DISCORD_ENABLED", "false").lower() == "true",
            "webhook_url": os.getenv("DISCORD_WEBHOOK_URL"),
        },
        "PUSHOVER": {
            "enabled": os.getenv("PUSHOVER_ENABLED", "false").lower() == "true",
            "api_token": os.getenv("PUSHOVER_API_TOKEN"),
            "user_key": os.getenv("PUSHOVER_USER_KEY"),
        },
    },
    "RATE_LIMITING": {
        "delay_between_notifications": 15,
        "delay_between_customers": 25,
        "max_retries": 3,
    },
}

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
