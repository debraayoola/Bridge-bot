import logging
import asyncio
from typing import Optional
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import Config

logger = logging.getLogger(__name__)

class TelegramHandler:
    """Handles Telegram bot operations."""
    
    def __init__(self, bridge):
        self.bridge = bridge
        self.config = Config()
        self.application = None
        self.bot = None
    
    async def start(self):
        """Start the Telegram bot."""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info("Connecting to Telegram...")
                
                # Build the application
                self.application = (
                    Application.builder()
                    .token(self.config.TELEGRAM_TOKEN)
                    .build()
                )
                
                # Register handlers
                self._register_handlers()
                
                # Start the bot
                await self.application.initialize()
                await self.application.start()
                
                # Get bot info
                self.bot = await self.application.bot.get_me()
                logger.info(f"Telegram Connected as @{self.bot.username}")
                
                # Start polling with error handling
                await self.application.updater.start_polling(
                    allowed_updates=["message", "edited_message", "callback_query"],
                    drop_pending_updates=True
                )
                
                # Keep the bot running
                while self.bridge.is_running:
                    await asyncio.sleep(1)
                
                break
                
            except Exception as e:
                logger.error(f"Telegram connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    raise
    
    async def stop(self):
        """Stop the Telegram bot."""
        try:
            if self.application:
                if self.application.updater:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
    
    def _register_handlers(self):
        """Register message and command handlers."""
        if not self.application:
            return
        
        # Message handlers
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE,
                self.handle_message
            )
        )
        
        self.application.add_handler(
            MessageHandler(
                filters.PHOTO & ~filters.UpdateType.EDITED_MESSAGE,
                self.handle_message
            )
        )
        
        self.application.add_handler(
            MessageHandler(
                filters.VIDEO & ~filters.UpdateType.EDITED_MESSAGE,
                self.handle_message
            )
        )
        
        self.application.add_handler(
            MessageHandler(
                filters.Document.ALL & ~filters.UpdateType.EDITED_MESSAGE,
                self.handle_message
            )
        )
        
        self.application.add_handler(
            MessageHandler(
                filters.AUDIO & ~filters.UpdateType.EDITED_MESSAGE,
                self.handle_message
            )
        )
        
        self.application.add_handler(
            MessageHandler(
                filters.VOICE & ~filters.UpdateType.EDITED_MESSAGE,
                self.handle_message
            )
        )
        
        self.application.add_handler(
            MessageHandler(
                filters.Sticker.ALL & ~filters.UpdateType.EDITED_MESSAGE,
                self.handle_message
            )
        )
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram messages."""
        try:
            # Skip messages not in the target chat
            if update.effective_chat.id != self.config.TELEGRAM_CHAT_ID:
                logger.debug(f"Ignoring message from chat {update.effective_chat.id}")
                return
            
            # Forward to Discord
            await self.bridge.forward_telegram_to_discord(update, context)
            
        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if update.effective_chat.id == self.config.TELEGRAM_CHAT_ID:
            await update.message.reply_text(
                "🤖 Bridge bot is active!\n"
                "Messages sent here will be forwarded to Discord."
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if update.effective_chat.id == self.config.TELEGRAM_CHAT_ID:
            await update.message.reply_text(
                "📚 **Bridge Bot Help**\n\n"
                "This bot bridges messages between Telegram and Discord.\n\n"
                "**Supported media:**\n"
                "• Text messages\n"
                "• Photos\n"
                "• Videos\n"
                "• Documents\n"
                "• Audio files\n"
                "• Voice messages\n"
                "• Stickers\n\n"
                "**Commands:**\n"
                "/start - Show bot status\n"
                "/help - Show this help message\n"
                "/status - Check bridge status"
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if update.effective_chat.id == self.config.TELEGRAM_CHAT_ID:
            status = "🟢 Running" if self.bridge.is_running else "🔴 Stopped"
            await update.message.reply_text(
                f"**Bridge Status:** {status}\n"
                f"**Telegram:** Connected\n"
                f"**Discord:** {'Connected' if self.bridge.discord.channel else 'Disconnected'}"
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors from Telegram."""
        logger.error(f"Telegram error: {context.error}")
        
        # Send error notification to the target chat
        try:
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    text=f"⚠️ An error occurred: {str(context.error)[:200]}"
                )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    async def send_message(self, text: str):
        """Send a message to Telegram."""
        try:
            # Split if too long (Telegram limit is 4096)
            if len(text) > 4096:
                chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
                for chunk in chunks:
                    await self.application.bot.send_message(
                        chat_id=self.config.TELEGRAM_CHAT_ID,
                        text=chunk,
                        parse_mode='Markdown'
                    )
            else:
                await self.application.bot.send_message(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    text=text,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
    
    async def send_photo(self, file_path: str, caption: str = None):
        """Send a photo to Telegram."""
        try:
            with open(file_path, 'rb') as f:
                await self.application.bot.send_photo(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    photo=f,
                    caption=caption,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending photo to Telegram: {e}")
    
    async def send_video(self, file_path: str, caption: str = None):
        """Send a video to Telegram."""
        try:
            with open(file_path, 'rb') as f:
                await self.application.bot.send_video(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    video=f,
                    caption=caption,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending video to Telegram: {e}")
    
    async def send_document(self, file_path: str, caption: str = None):
        """Send a document to Telegram."""
        try:
            with open(file_path, 'rb') as f:
                await self.application.bot.send_document(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    document=f,
                    caption=caption,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending document to Telegram: {e}")
    
    async def send_audio(self, file_path: str, caption: str = None):
        """Send audio to Telegram."""
        try:
            with open(file_path, 'rb') as f:
                await self.application.bot.send_audio(
                    chat_id=self.config.TELEGRAM_CHAT_ID,
                    audio=f,
                    caption=caption,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending audio to Telegram: {e}")
