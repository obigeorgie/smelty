import os
import sys
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_api_keys():
    """Validate required API keys are present and in correct format."""
    missing_keys = []
    warnings = []

    # Required key
    if not os.getenv('DISCORD_TOKEN'):
        missing_keys.append('DISCORD_TOKEN')

    # Primary API key
    if not os.getenv('DEEPSEEK_API_KEY'):
        missing_keys.append('DEEPSEEK_API_KEY')
    elif not os.getenv('DEEPSEEK_API_KEY').startswith('sk-'):
        warnings.append('DEEPSEEK_API_KEY format appears incorrect (should start with sk-)')

    # Fallback API key
    if not os.getenv('HUGGINGFACE_TOKEN'):
        warnings.append('HUGGINGFACE_TOKEN not found - fallback API will not be available')

    if missing_keys:
        logger.error(f"Missing required API keys: {', '.join(missing_keys)}")
        logger.error("Please set these environment variables before starting the bot.")
        sys.exit(1)

    if warnings:
        for warning in warnings:
            logger.warning(warning)

# Validate API keys on import
validate_api_keys()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')

# API endpoints
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-r1"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 5
COOLDOWN_PERIOD = 60  # seconds

# Cache configuration
CACHE_TIMEOUT = 300  # 5 minutes

# Database
DATABASE_PATH = "discord_bot.db"

logger.info("Configuration loaded successfully")
logger.debug(f"Using DeepSeek API URL: {DEEPSEEK_API_URL}")
logger.debug("Discord token present: %s", bool(DISCORD_TOKEN))
logger.debug("DeepSeek API key present: %s", bool(DEEPSEEK_API_KEY))
logger.debug("HuggingFace token present: %s", bool(HUGGINGFACE_TOKEN))