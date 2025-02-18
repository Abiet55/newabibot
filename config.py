import os
import json
import logging
from typing import Dict

# Set up logging
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

# Admin user IDs (verified)
ADMIN_IDS = [7715819534, 5545933865]  # List of admin Telegram user IDs

# Validate admin IDs
if not ADMIN_IDS:
    raise ValueError("No admin IDs configured. At least one admin ID is required.")
for admin_id in ADMIN_IDS:
    if not isinstance(admin_id, int):
        raise ValueError(f"Invalid admin ID format: {admin_id}. Admin IDs must be integers.")

# Available services configuration
AVAILABLE_SERVICES = {
    "premium": [
        "Telegram Premium - 1 Month",
        "Telegram Premium - 3 Months",
        "Telegram Premium - 6 Months",
        "Telegram Premium - 1 Year"
    ],
    "other": [
        "Telegram Stars"
    ]
}

# Load prices from JSON file
PRICES_FILE = "prices.json"

def load_prices() -> Dict[str, float]:
    """Load prices from the JSON file."""
    try:
        if os.path.exists(PRICES_FILE):
            with open(PRICES_FILE, 'r') as f:
                prices = json.load(f)
                return {k: round(float(v), 2) for k, v in prices.items()}
        else:
            logger.warning(f"Price file {PRICES_FILE} not found")
            return {}
    except Exception as e:
        logger.error(f"Error loading prices: {str(e)}")
        return {}

# Initialize services with prices
SERVICES = load_prices()

# Payment methods and details
PAYMENT_METHODS = ["TeleBirr", "CBE"]

PAYMENT_DETAILS = {
    "TeleBirr": {
        "phone": "096139850",
        "name": "Abdisa Feleke"
    },
    "CBE": {
        "account": "010000006623",
        "name": "Abdisa Feleke"
    }
}

# Order statuses
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_COMPLETED = "completed"

# Bot messages
WELCOME_MESSAGE = """
Welcome to our Service Bot! 🤖

We offer premium Telegram services with secure payment options.
Use /menu to see available options or /help for assistance.
"""

HELP_MESSAGE = """
Available commands:
/start - Start the bot
/menu - Show main menu
/help - Show this help message

Use the buttons below to navigate through the bot's features.

Available Premium Services:
• Telegram Premium - 1 Month
• Telegram Premium - 3 Months
• Telegram Premium - 6 Months
• Telegram Premium - 1 Year
"""