# Discord ↔ Telegram Bridge Bot

A production-ready bridge bot that synchronizes messages between a Discord channel and a Telegram group. Built with Python 3.12, using discord.py and python-telegram-bot.

## Features

- **Bidirectional Messaging**: Forward messages from Discord to Telegram and vice versa
- **Media Support**: Images, videos, GIFs, documents, audio, voice notes, and stickers
- **Sender Attribution**: Shows original sender's username
- **Anti-Loop Protection**: Prevents infinite forwarding
- **Automatic Reconnection**: Handles network failures gracefully
- **Production Ready**: Deploys on Render Free Web Service
- **No Database**: Uses environment variables for configuration

## Prerequisites

- Python 3.12+
- Discord Bot Token
- Telegram Bot Token
- Render account (for deployment) or any Python hosting

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord-telegram-bridge.git
cd discord-telegram-bridge
Telegram Setup

Creating a Bot with @BotFather

Open Telegram and search for @BotFather
Send /newbot command
Choose a name for your bot (e.g., "My Bridge Bot")
Choose a username ending with bot (e.g., mybridge_bot)
Copy the API token provided by BotFather
Disable Privacy Mode

IMPORTANT: By default, Telegram bots cannot see messages from other users. You must disable privacy mode:

Send /setprivacy to @BotFather
Select your bot
Choose Disable
Adding the Bot to a Group

Open your Telegram group
Click on group name → Add Members
Search for your bot's username
Add the bot to the group
Making the Bot Administrator

Click on group name → Administrators
Add the bot as administrator
Grant at least these permissions:

Send Messages
Delete Messages (optional)
Pin Messages (optional)
Obtaining TELEGRAM_CHAT_ID

Method 1: Using @userinfobot

Add @userinfobot to your group
Type /start in the group
The bot will show the chat ID
Method 2: Using your bot

Add your bot to the group
Send a message to the group
Check the bot's logs for chat_id
Method 3: Using the API

python
import requests
token = "YOUR_BOT_TOKEN"
response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
print(response.json())
Testing the Telegram Bot

Send a message to your bot in a private chat
The bot should reply with status information
Send a message in the group to test forwarding
Discord Setup

Create Application

Go to Discord Developer Portal
Click "New Application" and give it a name
Go to the "Bot" section in the left sidebar
Create Bot

Click "Add Bot" and confirm
Under the "TOKEN" section, click "Copy" to save your bot token
Never share this token!
Enable Message Content Intent

In the "Bot" section, scroll to "Privileged Gateway Intents"
Enable "MESSAGE CONTENT INTENT"
Enable "SERVER MEMBERS INTENT" (optional)
Save changes
Invite Bot

Go to "OAuth2" → "URL Generator"
Under "Scopes", select:

Bot
applications.commands (optional)
Under "Bot Permissions", select:

Send Messages
Read Messages
Attach Files
Read Message History
Use Slash Commands (optional)
Copy the generated URL and open it in your browser
Select your server and authorize the bot
Get Channel ID

Method 1: Developer Mode

Go to Discord Settings → Advanced
Enable "Developer Mode"
Right-click on your channel
Select "Copy ID"
Method 2: Using the Bot
The bot will log the channel it connects to on startup.

Environment Variables

Variable	Description	Required
DISCORD_TOKEN	Discord bot token from Developer Portal	Yes
DISCORD_CHANNEL_ID	ID of the Discord channel to monitor	Yes
TELEGRAM_TOKEN	Telegram bot token from @BotFather	Yes
TELEGRAM_CHAT_ID	ID of the Telegram group/chat	Yes
PORT	Port for Flask web server	No (default: 10000)
Deployment on Render

Quick Deploy

Push your repository to GitHub
Create a new Web Service on Render
Connect your GitHub repository
Use these settings:

Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: python bot.py
Using render.yaml

Create a render.yaml file (included in the repository)
Push to GitHub
Render will automatically detect and deploy
Manual Deployment

Create a new Web Service on Render
Connect your GitHub repository
Set the following environment variables in Render dashboard:

DISCORD_TOKEN
DISCORD_CHANNEL_ID
TELEGRAM_TOKEN
TELEGRAM_CHAT_ID
Click "Create Web Service"
Troubleshooting

Common Errors

"Missing required environment variables"

Ensure all four required variables are set in your .env file or Render environment.

"Discord Connected" but no messages forwarded

Check that the bot has the Message Content Intent enabled
Verify the bot has Send Messages permissions
Check that DISCORD_CHANNEL_ID is correct
"Telegram Connected" but no messages forwarded

Verify the bot is added to the group
Check that privacy mode is disabled
Confirm TELEGRAM_CHAT_ID is correct
Bot doesn't see messages from other users in Telegram

Privacy mode is likely still enabled
Send /setprivacy to @BotFather again
Select your bot and choose "Disable"
Files not forwarding

Check file size limits (Discord: 25MB, Telegram: 50MB for free tier)
Verify the downloads directory has write permissions
Check disk space
Network Issues

The bot automatically handles reconnection for both Discord and Telegram. Logs will show:

"Discord Reconnect Successful" when reconnected
"Telegram Reconnect Successful" when reconnected
Checking Logs

On Render: Go to your service → Logs
Locally: Check console output
FAQ

Q: Can I bridge multiple channels/groups?
A: Currently, the bot supports one Discord channel and one Telegram group. The architecture is designed to support multiple channels in future updates.

Q: How do I update the bot?
A: Push changes to your GitHub repository. If auto-deploy is enabled on Render, it will automatically redeploy.

Q: Will messages from bots be forwarded?
A: No, messages from bots are ignored on both platforms to prevent loops.

Q: What about formatting?
A: Discord messages are sent as plain text to Telegram. Telegram messages are sent as plain text to Discord.

Q: How are replies handled?
A: Replies are forwarded with the sender's name but may not retain reply threading.

Q: The bot keeps restarting on Render
A: Check the logs for errors. Common issues: missing environment variables, invalid tokens, or permission problems.

Q: Can I use this on other platforms?
A: This bot is specifically designed for Discord and Telegram. For other platforms, you'd need to modify the code.

Q: Is there a web interface?
A: The bot includes a minimal Flask web server for health checks, but no admin interface.

Security Notes

Never commit your .env file to version control
Keep your bot tokens secret
The bot doesn't store any user data
All files are stored temporarily and deleted after forwarding
License

MIT License - feel free to use, modify, and distribute.

Contributing

Contributions are welcome! Please:

Fork the repository
Create a feature branch
Submit a pull request
Support

For issues and questions:

Open an issue on GitHub
Check the logs for error messages
Future Improvements

The architecture is designed to support:

Multiple Discord channels
Multiple Telegram groups
SQLite for persistent configuration
Admin commands
Webhook mode
Docker containerization
Command-line configuration
Advanced logging and monitoring
