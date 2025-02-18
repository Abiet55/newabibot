import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import (
    ADMIN_IDS, SERVICES, STATUS_PENDING, STATUS_APPROVED,
    STATUS_REJECTED, STATUS_COMPLETED, WELCOME_MESSAGE, HELP_MESSAGE,
    PAYMENT_DETAILS, AVAILABLE_SERVICES
)
from storage import Storage
from keyboards import (
    get_services_keyboard,
    get_payment_methods_keyboard,
    get_admin_approval_keyboard,
    get_main_menu_keyboard,
    get_premium_duration_keyboard,
    get_payment_confirmation_keyboard
)
from datetime import datetime

logger = logging.getLogger(__name__)
storage = Storage()

async def is_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE = None) -> bool:
    """Check if a user has admin privileges."""
    logger.info(f"🔒 Admin Access Check - User ID: {user_id}")
    logger.info(f"📋 Current admin IDs: {ADMIN_IDS}")

    is_admin = user_id in ADMIN_IDS
    logger.info(f"🔑 Admin check result for user {user_id}: {'✅ Approved' if is_admin else '❌ Denied'}")

    if context and not is_admin:
        logger.warning(f"⚠️ Unauthorized admin access attempt by user {user_id}")
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ This command is only available to administrators."
        )
    return is_admin

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    logger.info(f"User {update.message.from_user.id} started the bot")
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    logger.info(f"User {update.message.from_user.id} requested help")
    await update.message.reply_text(HELP_MESSAGE)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /menu command."""
    logger.info(f"User {update.message.from_user.id} opened the menu")
    await update.message.reply_text(
        "Please select an option:",
        reply_markup=get_main_menu_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "place_order":
        await query.message.edit_text(
            "🛍️ Please select a service:",
            reply_markup=get_services_keyboard()
        )

    elif query.data == "telegram_premium":
        await query.message.edit_text(
            "🌟 Telegram Premium Subscription\n"
            "━━━━━━━━━━━━━━━\n"
            "Choose your preferred subscription duration:\n\n"
            "All plans include:\n"
            "• Premium stickers and reactions\n"
            "• 4GB file uploads\n"
            "• Faster downloads\n"
            "• Voice-to-text conversion\n"
            "• Ad-free experience\n"
            "• Unique badge and profile features\n\n"
            "Select a plan that suits you best:",
            reply_markup=get_premium_duration_keyboard()
        )

    elif query.data.startswith("premium_"):
        duration = query.data.replace("premium_", "")
        duration_display = {
            "1month": "1 Month",
            "3months": "3 Months",
            "6months": "6 Months",
            "1year": "1 Year"
        }

        service_name = f"Telegram Premium - {duration_display[duration]}"
        order_id = storage.create_order(query.from_user.id, service_name)
        price = SERVICES.get(service_name, 0)

        await query.message.edit_text(
            f"✨ Telegram Premium Order Created!\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📋 Order Details:\n"
            f"🔖 Order ID: {order_id}\n"
            f"📦 Package: {service_name}\n"
            f"💰 Price: ${price}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"Your order will be reviewed shortly.",
            reply_markup=get_main_menu_keyboard()
        )

        # Notify admins
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🔔 New Premium Order\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🔖 Order ID: {order_id}\n"
                f"👤 User ID: {query.from_user.id}\n"
                f"📦 Package: {service_name}\n"
                f"💰 Price: ${price}\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"━━━━━━━━━━━━━━━",
                reply_markup=get_admin_approval_keyboard(order_id, "order")
            )

    elif query.data.startswith("payment_"):
        payment_method = query.data.replace("payment_", "")
        user_id = query.from_user.id
        order_id = storage.get_user_session(user_id, "current_order")

        if order_id and storage.update_payment_method(order_id, payment_method):
            order = storage.get_order(order_id)
            payment_info = PAYMENT_DETAILS.get(payment_method, {})

            payment_details = f"\n{payment_method} Payment Details:\n"
            if payment_method == "TeleBirr":
                payment_details += f"📱 Phone: {payment_info['phone']}\n"
            else:
                payment_details += f"💳 Account: {payment_info['account']}\n"
            payment_details += f"👤 Name: {payment_info['name']}\n"

            await query.message.edit_text(
                f"💫 Payment Information\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🔖 Order ID: {order_id}\n"
                f"🛠️ Service: {order['service']}\n"
                f"💳 Method: {payment_method}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"{payment_details}\n"
                f"Please make the payment and click 'I've Made the Payment' once completed.",
                reply_markup=get_payment_confirmation_keyboard(payment_method, order_id)
            )

    elif query.data.startswith("confirm_payment_"):
        parts = query.data.split("_", 3)
        if len(parts) == 4:
            _, _, payment_method, order_id = parts
            await handle_payment_confirmation(query, context, payment_method, order_id)

    elif query.data in ["back_to_menu", "back_to_services"]:
        if query.data == "back_to_menu":
            await query.message.edit_text(
                "Main Menu:",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await query.message.edit_text(
                "🛍️ Please select a service:",
                reply_markup=get_services_keyboard()
            )

async def handle_payment_confirmation(query, context, payment_method, order_id):
    """Handle payment confirmation with enhanced security and logging."""
    try:
        order = storage.get_order(order_id)
        if not order:
            logger.error(f"Payment confirmation failed - Order {order_id} not found")
            await query.message.edit_text(
                "❌ Order not found. Please contact support.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        if order['payment_status'] == 'confirmed':
            logger.warning(f"Duplicate payment confirmation attempt for order {order_id}")
            await query.message.edit_text(
                "⚠️ Payment already confirmed for this order.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        # Update order with payment confirmation
        order['payment_status'] = 'confirmed'
        order['payment_confirmation_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        await query.message.edit_text(
            f"✅ Payment Confirmation Received!\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Thank you for your payment. Our team will verify it shortly.\n\n"
            f"Order Details:\n"
            f"🔖 Order ID: {order_id}\n"
            f"🛠️ Service: {order['service']}\n"
            f"💳 Payment Method: {payment_method}\n"
            f"━━━━━━━━━━━━━━━",
            reply_markup=get_main_menu_keyboard()
        )

        # Detailed notification for admins
        payment_info = PAYMENT_DETAILS.get(payment_method, {})
        admin_message = (
            f"💰 New Payment Confirmation\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🔖 Order ID: {order_id}\n"
            f"👤 User ID: {query.from_user.id}\n"
            f"🛠️ Service: {order['service']}\n"
            f"💳 Method: {payment_method}\n"
            f"📅 Confirmation Time: {order['payment_confirmation_time']}\n"
            f"💳 Payment Account: {payment_info.get('account', payment_info.get('phone', 'N/A'))}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Please verify the payment and process the order."
        )

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    reply_markup=get_admin_approval_keyboard(order_id, "payment")
                )
                logger.info(f"Payment confirmation notification sent to admin {admin_id} for order {order_id}")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id} about payment confirmation: {str(e)}")

    except Exception as e:
        logger.error(f"Error processing payment confirmation for order {order_id}: {str(e)}")
        await query.message.edit_text(
            "❌ An error occurred while processing your payment confirmation.\n"
            "Please try again or contact support.",
            reply_markup=get_main_menu_keyboard()
        )

async def handle_admin_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not await is_admin(user_id):
        logger.warning(f"Unauthorized admin action attempt by user {user_id}")
        return

    try:
        action, item_type, item_id = query.data.split("_", 2)
        logger.info(f"Admin {user_id} performing {action} on {item_type} {item_id}")

        if item_type == "order":
            order = storage.get_order(item_id)
            if not order:
                logger.error(f"Order {item_id} not found for admin approval")
                await query.message.edit_text(
                    "❌ Error: Order not found",
                    reply_markup=None
                )
                return

            if action == "approve":
                storage.update_order_status(item_id, STATUS_APPROVED)
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"✅ Order Approved!\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔖 Order ID: {item_id}\n"
                    f"Please select your payment method:",
                    reply_markup=get_payment_methods_keyboard()
                )
                storage.set_user_session(order["user_id"], "current_order", item_id)
                logger.info(f"Order {item_id} approved by admin {user_id}")
            else:
                storage.update_order_status(item_id, STATUS_REJECTED)
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"❌ Order Rejected\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"🔖 Order ID: {item_id}",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"Order {item_id} rejected by admin {user_id}")

            await query.message.edit_text(
                f"{item_type.capitalize()} has been {action}d.",
                reply_markup=None
            )

        elif item_type == "payment":
            order = storage.get_order(item_id)
            if not order:
                logger.error(f"Payment verification failed - Order {item_id} not found")
                await query.message.edit_text("❌ Payment verification failed - Order not found")
                return

            if action == "approve":
                storage.update_order_status(item_id, STATUS_COMPLETED)
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"🎉 Payment Verified!\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"Your order {item_id} is now complete.\n"
                    f"Thank you for your purchase!",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"Payment for order {item_id} approved by admin {user_id}")
            else:
                await context.bot.send_message(
                    chat_id=order["user_id"],
                    text=f"❌ Payment Verification Failed\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"Order ID: {item_id}\n"
                    f"Please try again or contact support.",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"Payment for order {item_id} rejected by admin {user_id}")

            await query.message.edit_text(
                f"Payment for order {item_id} has been {action}d.",
                reply_markup=None
            )

    except ValueError:
        logger.error(f"Invalid callback data format: {query.data}")
        await query.message.edit_text(
            "❌ Error: Invalid approval format",
            reply_markup=None
        )

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    feedback_text = update.message.text
    feedback_id = storage.add_feedback(user_id, feedback_text)

    await update.message.reply_text(
        "✨ Thank you for your feedback!\n"
        "━━━━━━━━━━━━━━━\n"
        "Our team will review it shortly.",
        reply_markup=get_main_menu_keyboard()
    )

    # Notify admins
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"💬 New Feedback\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 User ID: {user_id}\n"
            f"📝 Feedback: {feedback_text}\n"
            f"━━━━━━━━━━━━━━━",
            reply_markup=get_admin_approval_keyboard(str(feedback_id), "feedback")
        )