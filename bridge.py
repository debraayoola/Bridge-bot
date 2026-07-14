import logging
import asyncio
from typing import Optional, Dict, Any
from collections import deque
import discord
from telegram import Update, Message as TelegramMessage
from telegram.ext import ContextTypes

from config import Config
from utils import FileManager, format_sender_name, is_bot_message
from discord_handler import DiscordHandler
from telegram_handler import TelegramHandler

logger = logging.getLogger(__name__)

class Bridge:
    """Main bridge class that coordinates between Discord and Telegram."""
    
    def __init__(self):
        self.config = Config()
        self.file_manager = FileManager(Config.DOWNLOAD_DIR)
        self.discord = DiscordHandler(self)
        self.telegram = TelegramHandler(self)
        self._message_cache = deque(maxlen=1000)  # Prevent loops
        self._running = False
        self._tasks = []
    
    @property
    def is_running(self) -> bool:
        """Check if the bridge is running."""
        return self._running
    
    async def start(self):
        """Start both Discord and Telegram handlers."""
        try:
            self._running = True
            logger.info("Starting bridge...")
            
            # Start Discord
            discord_task = asyncio.create_task(self.discord.start())
            self._tasks.append(discord_task)
            
            # Start Telegram
            telegram_task = asyncio.create_task(self.telegram.start())
            self._tasks.append(telegram_task)
            
            # Wait for both to finish (they run forever)
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Bridge error: {e}")
            self._running = False
            raise
    
    async def stop(self):
        """Stop the bridge and clean up resources."""
        self._running = False
        logger.info("Stopping bridge...")
        
        # Stop Discord
        await self.discord.stop()
        
        # Stop Telegram
        await self.telegram.stop()
        
        # Clean up temp files
        self.file_manager.cleanup_directory()
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Bridge stopped")
    
    def is_forwarded_message(self, message_id: int, platform: str) -> bool:
        """Check if a message has already been forwarded."""
        key = f"{platform}:{message_id}"
        return key in self._message_cache
    
    def mark_as_forwarded(self, message_id: int, platform: str):
        """Mark a message as forwarded to prevent loops."""
        key = f"{platform}:{message_id}"
        self._message_cache.append(key)
    
    async def forward_discord_to_telegram(self, discord_message: discord.Message):
        """Forward a Discord message to Telegram."""
        try:
            # Skip bot messages
            if discord_message.author.bot:
                logger.debug("Skipping bot message from Discord")
                return
            
            # Check if already forwarded
            if self.is_forwarded_message(discord_message.id, 'discord'):
                logger.debug(f"Message {discord_message.id} already forwarded")
                return
            
            # Mark as forwarded
            self.mark_as_forwarded(discord_message.id, 'discord')
            
            # Format sender name
            sender_name = format_sender_name(
                discord_message.author.name,
                discord_message.author.display_name
            )
            
            # Check for attachments
            attachments = discord_message.attachments
            
            if attachments:
                # Handle media messages
                for attachment in attachments:
                    await self._forward_attachment_to_telegram(
                        attachment, 
                        discord_message.content,
                        sender_name
                    )
            elif discord_message.content:
                # Handle text messages
                await self.telegram.send_message(
                    f"**{sender_name}**: {discord_message.content}"
                )
                logger.info(f"Discord → Telegram: {sender_name}: {discord_message.content[:50]}...")
            
        except Exception as e:
            logger.error(f"Error forwarding Discord → Telegram: {e}")
    
    async def _forward_attachment_to_telegram(
        self, 
        attachment: discord.Attachment,
        caption: str,
        sender_name: str
    ):
        """Forward a single attachment to Telegram."""
        try:
            file_path = await self.file_manager.download_file(
                attachment.url,
                attachment.filename
            )
            
            if file_path and file_path.exists():
                caption_text = f"**{sender_name}**: {caption}" if caption else f"**{sender_name}**"
                
                # Determine file type and send appropriately
                if attachment.content_type and attachment.content_type.startswith('image'):
                    await self.telegram.send_photo(file_path, caption_text)
                elif attachment.content_type and attachment.content_type.startswith('video'):
                    await self.telegram.send_video(file_path, caption_text)
                elif attachment.content_type and attachment.content_type.startswith('audio'):
                    await self.telegram.send_audio(file_path, caption_text)
                else:
                    # Send as document
                    await self.telegram.send_document(file_path, caption_text)
                
                # Clean up
                self.file_manager.delete_file(file_path)
                logger.info(f"Discord → Telegram: {sender_name} sent {attachment.filename}")
                
        except Exception as e:
            logger.error(f"Error forwarding attachment {attachment.filename}: {e}")
    
    async def forward_telegram_to_discord(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Forward a Telegram message to Discord."""
        try:
            message = update.effective_message
            
            # Skip bot messages
            if message.from_user and message.from_user.is_bot:
                logger.debug("Skipping bot message from Telegram")
                return
            
            # Check if already forwarded
            if self.is_forwarded_message(message.message_id, 'telegram'):
                logger.debug(f"Message {message.message_id} already forwarded")
                return
            
            # Mark as forwarded
            self.mark_as_forwarded(message.message_id, 'telegram')
            
            # Get sender name
            sender_name = format_sender_name(
                message.from_user.username if message.from_user else None,
                message.from_user.full_name if message.from_user else None
            )
            
            # Check if it's a media message
            if message.photo:
                await self._forward_photo_to_discord(message, sender_name)
            elif message.video:
                await self._forward_video_to_discord(message, sender_name)
            elif message.document:
                await self._forward_document_to_discord(message, sender_name)
            elif message.audio:
                await self._forward_audio_to_discord(message, sender_name)
            elif message.voice:
                await self._forward_voice_to_discord(message, sender_name)
            elif message.sticker:
                await self._forward_sticker_to_discord(message, sender_name)
            elif message.text:
                await self.discord.send_message(f"**{sender_name}**: {message.text}")
                logger.info(f"Telegram → Discord: {sender_name}: {message.text[:50]}...")
                
        except Exception as e:
            logger.error(f"Error forwarding Telegram → Discord: {e}")
    
    async def _forward_photo_to_discord(self, message: TelegramMessage, sender_name: str):
        """Forward a photo from Telegram to Discord."""
        try:
            photo = message.photo[-1]  # Get the largest photo
            file = await context.bot.get_file(photo.file_id)
            file_path = await self._download_telegram_file(file, 'photo.jpg')
            
            if file_path:
                caption = message.caption or ""
                await self.discord.send_file(
                    file_path,
                    f"**{sender_name}**: {caption}" if caption else f"**{sender_name}**"
                )
                self.file_manager.delete_file(file_path)
                logger.info(f"Telegram → Discord: {sender_name} sent photo")
                
        except Exception as e:
            logger.error(f"Error forwarding photo: {e}")
    
    async def _forward_video_to_discord(self, message: TelegramMessage, sender_name: str):
        """Forward a video from Telegram to Discord."""
        try:
            file = await context.bot.get_file(message.video.file_id)
            filename = message.video.file_name or 'video.mp4'
            file_path = await self._download_telegram_file(file, filename)
            
            if file_path:
                caption = message.caption or ""
                await self.discord.send_file(
                    file_path,
                    f"**{sender_name}**: {caption}" if caption else f"**{sender_name}**"
                )
                self.file_manager.delete_file(file_path)
                logger.info(f"Telegram → Discord: {sender_name} sent video")
                
        except Exception as e:
            logger.error(f"Error forwarding video: {e}")
    
    async def _forward_document_to_discord(self, message: TelegramMessage, sender_name: str):
        """Forward a document from Telegram to Discord."""
        try:
            file = await context.bot.get_file(message.document.file_id)
            filename = message.document.file_name or 'document.pdf'
            file_path = await self._download_telegram_file(file, filename)
            
            if file_path:
                caption = message.caption or ""
                await self.discord.send_file(
                    file_path,
                    f"**{sender_name}**: {caption}" if caption else f"**{sender_name}**"
                )
                self.file_manager.delete_file(file_path)
                logger.info(f"Telegram → Discord: {sender_name} sent document")
                
        except Exception as e:
            logger.error(f"Error forwarding document: {e}")
    
    async def _forward_audio_to_discord(self, message: TelegramMessage, sender_name: str):
        """Forward audio from Telegram to Discord."""
        try:
            file = await context.bot.get_file(message.audio.file_id)
            filename = message.audio.file_name or 'audio.mp3'
            file_path = await self._download_telegram_file(file, filename)
            
            if file_path:
                caption = message.caption or ""
                await self.discord.send_file(
                    file_path,
                    f"**{sender_name}**: {caption}" if caption else f"**{sender_name}**"
                )
                self.file_manager.delete_file(file_path)
                logger.info(f"Telegram → Discord: {sender_name} sent audio")
                
        except Exception as e:
            logger.error(f"Error forwarding audio: {e}")
    
    async def _forward_voice_to_discord(self, message: TelegramMessage, sender_name: str):
        """Forward voice message from Telegram to Discord."""
        try:
            file = await context.bot.get_file(message.voice.file_id)
            file_path = await self._download_telegram_file(file, 'voice.ogg')
            
            if file_path:
                await self.discord.send_file(file_path, f"**{sender_name}** (Voice)")
                self.file_manager.delete_file(file_path)
                logger.info(f"Telegram → Discord: {sender_name} sent voice")
                
        except Exception as e:
            logger.error(f"Error forwarding voice: {e}")
    
    async def _forward_sticker_to_discord(self, message: TelegramMessage, sender_name: str):
        """Forward sticker from Telegram to Discord."""
        try:
            file = await context.bot.get_file(message.sticker.file_id)
            ext = 'webp' if message.sticker.is_animated else 'png'
            file_path = await self._download_telegram_file(file, f'sticker.{ext}')
            
            if file_path:
                await self.discord.send_file(file_path, f"**{sender_name}** sent a sticker")
                self.file_manager.delete_file(file_path)
                logger.info(f"Telegram → Discord: {sender_name} sent sticker")
                
        except Exception as e:
            logger.error(f"Error forwarding sticker: {e}")
    
    async def _download_telegram_file(self, file, filename: str):
        """Download a file from Telegram."""
        try:
            temp_path = self.file_manager.get_temp_path(filename)
            await file.download_to_drive(temp_path)
            logger.info(f"Downloaded Telegram file: {temp_path}")
            return temp_path
        except Exception as e:
            logger.error(f"Error downloading Telegram file: {e}")
            return None
