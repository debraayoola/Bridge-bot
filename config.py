import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the bridge bot."""
    
    # Discord configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
    
    # Telegram configuration
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID', 0))
    
    # Server configuration
    PORT = int(os.getenv('PORT', 10000))
    
    # Download directory
    DOWNLOAD_DIR = 'downloads'
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set."""
        missing = []
        if not cls.DISCORD_TOKEN:
            missing.append('DISCORD_TOKEN')
        if not cls.DISCORD_CHANNEL_ID:
            missing.append('DISCORD_CHANNEL_ID')
        if not cls.TELEGRAM_TOKEN:
            missing.append('TELEGRAM_TOKEN')
        if not cls.TELEGRAM_CHAT_ID:
            missing.append('TELEGRAM_CHAT_ID')
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        
        return True
