#!/usr/bin/env python3
"""
Discord ↔ Telegram Bridge Bot
Main entry point for the application.
"""

import os
import sys
import logging
import asyncio
import signal
from threading import Thread
from flask import Flask

# Ensure the downloads directory exists
os.makedirs('downloads', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set lower log levels for noisy libraries
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord.client').setLevel(logging.WARNING)
logging.getLogger('discord.gateway').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Import after logging configuration
from config import Config
from bridge import Bridge
from app import app

class BotRunner:
    """Main bot runner class."""
    
    def __init__(self):
        self.bridge = None
        self.flask_thread = None
        self.loop = None
        self._shutdown_event = asyncio.Event()
    
    def run_flask(self):
        """Run Flask app in a separate thread."""
        try:
            # Get port from environment or use default
            port = int(os.getenv('PORT', 10000))
            app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"Flask server error: {e}")
    
    async def shutdown(self, signal=None):
        """Gracefully shutdown the bot."""
        logger.info(f"Received shutdown signal: {signal}")
        self._shutdown_event.set()
        
        if self.bridge:
            logger.info("Stopping bridge...")
            await self.bridge.stop()
            self.bridge = None
        
        logger.info("Shutdown complete")
    
    async def run(self):
        """Main async run method."""
        try:
            # Validate configuration
            try:
                Config.validate()
                logger.info("Configuration validated successfully")
            except ValueError as e:
                logger.error(f"Configuration error: {e}")
                return
            
            # Start Flask in background thread
            self.flask_thread = Thread(target=self.run_flask, daemon=True)
            self.flask_thread.start()
            logger.info(f"Flask server started on port {Config.PORT}")
            
            # Create and start bridge
            self.bridge = Bridge()
            await self.bridge.start()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            await self.shutdown()

def run_bot():
    """Entry point for the bot."""
    runner = BotRunner()
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda s=sig: asyncio.create_task(runner.shutdown(s))
        )
    
    try:
        loop.run_until_complete(runner.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        # Clean up
        try:
            # Cancel all running tasks
            tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)]
            if tasks:
                for task in tasks:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info("Bot stopped")

if __name__ == '__main__':
    run_bot()
