import discord
import logging
import asyncio
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)

class DiscordHandler:
    """Handles Discord bot operations."""
    
    def __init__(self, bridge):
        self.bridge = bridge
        self.config = Config()
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.messages = True
        self.intents.guilds = True
        self.client = discord.Client(intents=self.intents)
        self.channel = None
        
        # Register event handlers
        @self.client.event
        async def on_ready():
            await self.on_ready()
        
        @self.client.event
        async def on_message(message):
            await self.on_message(message)
        
        @self.client.event
        async def on_disconnect():
            await self.on_disconnect()
        
        @self.client.event
        async def on_resumed():
            await self.on_resumed()
    
    async def start(self):
        """Start the Discord client."""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info("Connecting to Discord...")
                await self.client.start(self.config.DISCORD_TOKEN)
                break
            except Exception as e:
                logger.error(f"Discord connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    raise
    
    async def stop(self):
        """Stop the Discord client."""
        try:
            await self.client.close()
            logger.info("Discord client closed")
        except Exception as e:
            logger.error(f"Error closing Discord client: {e}")
    
    async def on_ready(self):
        """Handle Discord ready event."""
        try:
            logger.info(f"Discord Connected")
            logger.info(f"Logged in as {self.client.user.name}")
            
            # Get the channel
            self.channel = self.client.get_channel(self.config.DISCORD_CHANNEL_ID)
            if not self.channel:
                # Try to fetch the channel
                try:
                    self.channel = await self.client.fetch_channel(self.config.DISCORD_CHANNEL_ID)
                except Exception as e:
                    logger.error(f"Could not find Discord channel: {e}")
                    return
            
            logger.info(f"Connected to Discord channel: {self.channel.name if self.channel else 'Unknown'}")
            
        except Exception as e:
            logger.error(f"Error in on_ready: {e}")
    
    async def on_message(self, message: discord.Message):
        """Handle incoming Discord messages."""
        try:
            # Skip messages from the bot itself
            if message.author.id == self.client.user.id:
                return
            
            # Skip messages not in the target channel
            if message.channel.id != self.config.DISCORD_CHANNEL_ID:
                return
            
            # Skip system messages
            if message.type != discord.MessageType.default:
                logger.debug(f"Skipping system message type: {message.type}")
                return
            
            # Forward to Telegram
            await self.bridge.forward_discord_to_telegram(message)
            
        except Exception as e:
            logger.error(f"Error in on_message: {e}")
    
    async def on_disconnect(self):
        """Handle Discord disconnect."""
        logger.warning("Discord disconnected")
    
    async def on_resumed(self):
        """Handle Discord connection resumed."""
        logger.info("Discord Reconnect Successful")
    
    async def send_message(self, content: str):
        """Send a message to Discord."""
        try:
            if not self.channel:
                logger.error("Discord channel not available")
                return
            
            # Split message if too long (Discord limit is 2000)
            if len(content) > 2000:
                chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                for chunk in chunks:
                    await self.channel.send(chunk)
            else:
                await self.channel.send(content)
                
        except discord.Forbidden as e:
            logger.error(f"Missing permissions to send message to Discord: {e}")
        except discord.HTTPException as e:
            logger.error(f"HTTP error sending message to Discord: {e}")
        except Exception as e:
            logger.error(f"Error sending message to Discord: {e}")
    
    async def send_file(self, file_path, caption: Optional[str] = None):
        """Send a file to Discord."""
        try:
            if not self.channel:
                logger.error("Discord channel not available")
                return
            
            file = discord.File(file_path)
            await self.channel.send(content=caption, file=file)
            
        except discord.Forbidden as e:
            logger.error(f"Missing permissions to send file to Discord: {e}")
        except discord.HTTPException as e:
            logger.error(f"HTTP error sending file to Discord: {e}")
        except Exception as e:
            logger.error(f"Error sending file to Discord: {e}")
    
    async def send_embed(self, embed: discord.Embed):
        """Send an embed to Discord."""
        try:
            if not self.channel:
                logger.error("Discord channel not available")
                return
            
            await self.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error sending embed to Discord: {e}")
