from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import SERVICES, PAYMENT_METHODS, AVAILABLE_SERVICES

def get_services_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="📱 Telegram Premium", callback_data="telegram_premium")],
        [InlineKeyboardButton(text="⭐ Telegram Stars", callback_data="telegram_stars")],
        [InlineKeyboardButton(text="↩️ Back to Main Menu", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_premium_duration_keyboard():
    keyboard = []
    duration_map = {
        "Telegram Premium - 1 Month": ("1️⃣", "premium_1month"),
        "Telegram Premium - 3 Months": ("3️⃣", "premium_3months"),
        "Telegram Premium - 6 Months": ("6️⃣", "premium_6months"),
        "Telegram Premium - 1 Year": ("🗓️", "premium_1year")
    }

    for service, (emoji, callback) in duration_map.items():
        if service in AVAILABLE_SERVICES["premium"]:
            price = SERVICES.get(service, 0)
            display_price = f"${price:,.2f}" if price else "Price not set"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{emoji} {service.replace('Telegram Premium - ', '')} - {display_price}",
                    callback_data=callback if price else "price_not_set"
                )
            ])

    keyboard.append([InlineKeyboardButton(text="↩️ Back", callback_data="back_to_services")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_methods_keyboard():
    keyboard = []
    for method in PAYMENT_METHODS:
        keyboard.append([InlineKeyboardButton(text=f"💳 {method}", callback_data=f"payment_{method}")])
    keyboard.append([InlineKeyboardButton(text="↩️ Back to Main Menu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_confirmation_keyboard(payment_method: str, order_id: str):
    keyboard = [
        [InlineKeyboardButton(text="✅ I've Made the Payment", 
                            callback_data=f"confirm_payment_{payment_method}_{order_id}")],
        [InlineKeyboardButton(text="❌ Cancel Payment", 
                            callback_data="cancel_payment")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_approval_keyboard(item_id: str, item_type: str):
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Approve", 
                               callback_data=f"approve_{item_type}_{item_id}"),
            InlineKeyboardButton(text="❌ Reject", 
                               callback_data=f"reject_{item_type}_{item_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="🛍️ Place Order", callback_data="place_order")],
        [InlineKeyboardButton(text="📋 My Orders", callback_data="my_orders")],
        [InlineKeyboardButton(text="💬 Submit Feedback", callback_data="submit_feedback")]
    ]
    return InlineKeyboardMarkup(keyboard)