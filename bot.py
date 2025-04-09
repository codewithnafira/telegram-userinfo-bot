#!/usr/bin/env python3
"""
Telegram User Info Bot
- Shows detailed user info for forwarded messages
- /myid command to get your ID
- Inline buttons for interaction
- Privacy-aware handling
"""

import logging
import os
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UserInfoBot:
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(self.token).build()
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("myid", self.myid_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_message))
        self.app.add_handler(CallbackQueryHandler(self.handle_button_press))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send welcome message with inline keyboard"""
        keyboard = [
            [InlineKeyboardButton("Show My ID", callback_data="myid")],
            [InlineKeyboardButton("Help", callback_data="help")]
        ]
        await update.message.reply_text(
            "👋 Welcome to User Info Bot!\n\n"
            "I can show information about forwarded messages.\n\n"
            "Try these options:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def myid_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /myid command"""
        user = update.effective_user
        keyboard = [
            [InlineKeyboardButton("Refresh", callback_data="refresh_myid")]
        ]
        await update.message.reply_text(
            f"🆔 <b>Your Telegram ID</b>\n"
            f"├ ID: <code>{user.id}</code>\n"
            f"├ Username: @{user.username if user.username else 'N/A'}\n"
            f"└ Language: {user.language_code if user.language_code else 'N/A'}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help message"""
        await update.message.reply_text(
            "ℹ️ <b>Bot Help</b>\n\n"
            "<b>Commands:</b>\n"
            "/start - Welcome message\n"
            "/myid - Show your Telegram ID\n"
            "/help - This message\n\n"
            "<b>How to use:</b>\n"
            "1. Forward any message to see sender info\n"
            "2. Some info may be hidden due to privacy settings",
            parse_mode="HTML"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all incoming messages"""
        msg = update.message
        
        try:
            if hasattr(msg, 'forward_from') and msg.forward_from:
                await self.show_user_info(msg, msg.forward_from)
            elif hasattr(msg, 'forward_from_chat') and msg.forward_from_chat:
                await self.show_chat_info(msg, msg.forward_from_chat)
            elif hasattr(msg, 'forward_sender_name') and msg.forward_sender_name:
                await self.show_private_forward(msg)
            elif not msg.forward_date:  # Only respond to non-forwarded messages
                keyboard = [
                    [InlineKeyboardButton("What can I do?", callback_data="help")]
                ]
                await msg.reply_text(
                    "ℹ️ Forward me a message to see info about the sender",
                    reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await msg.reply_text("⚠️ An error occurred while processing your message")

    async def show_user_info(self, msg: Message, user):
        """Display user info with inline buttons"""
        keyboard = [
            [InlineKeyboardButton("Refresh", callback_data=f"refresh_user_{user.id}")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ]
        await msg.reply_text(
            f"👤 <b>User Information</b>\n"
            f"├ ID: <code>{user.id}</code>\n"
            f"├ Username: @{user.username if user.username else 'N/A'}\n"
            f"├ Bot: {'✅ Yes' if user.is_bot else '❌ No'}\n"
            f"└ Language: {user.language_code if user.language_code else 'N/A'}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_button_press(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all inline button presses"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "myid":
            user = query.from_user
            await query.edit_message_text(
                f"🆔 <b>Your ID</b>: <code>{user.id}</code>\n"
                f"👤 <b>Username</b>: @{user.username if user.username else 'N/A'}",
                parse_mode="HTML"
            )
        elif query.data == "help":
            await self.help_command(update, context)
        elif query.data == "close":
            await query.delete_message()

    def run(self):
        """Start the bot"""
        logger.info("Starting bot...")
        self.app.run_polling()

if __name__ == "__main__":
    # Load token from environment variable
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("Missing TELEGRAM_BOT_TOKEN in environment variables")
        exit(1)
    
    bot = UserInfoBot(TOKEN)
    bot.run()
