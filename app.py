import logging
from flask import Flask, jsonify

app = Flask(__name__)

# Configure logging for Flask
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    """Health check endpoint."""
    return jsonify({
        'status': 'running',
        'service': 'Discord-Telegram Bridge',
        'version': '1.0.0'
    })

@app.route('/health')
def health():
    """Detailed health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Bot is running'
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint."""
    return 'pong'

if __name__ == '__main__':
    # This is only for local testing, Render uses the start command
    from config import Config
    app.run(host='0.0.0.0', port=Config.PORT)
