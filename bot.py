import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from csv_handler import CSVHandler
from litellm_client import LiteLLMClient

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
LITELLM_API_URL = os.getenv('LITELLM_API_URL')
LITELLM_MASTER_KEY = os.getenv('LITELLM_MASTER_KEY')
USERS_CSV_PATH = os.getenv('USERS_CSV_PATH', 'users.csv')
DEFAULT_TEAM_NAME = os.getenv('DEFAULT_TEAM_NAME', 'StudentsNSTU')
DEFAULT_TOKEN_DURATION = os.getenv('DEFAULT_TOKEN_DURATION', '90m')
DEFAULT_TOKEN_BUDGET = os.getenv('DEFAULT_TOKEN_BUDGET', 0.5)

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
if not LITELLM_API_URL:
    raise ValueError("LITELLM_API_URL environment variable is required")
if not LITELLM_MASTER_KEY:
    raise ValueError("LITELLM_MASTER_KEY environment variable is required")

csv_handler = CSVHandler(USERS_CSV_PATH)
litellm_client = LiteLLMClient(LITELLM_API_URL, LITELLM_MASTER_KEY)


def is_authorized(func):
    """Decorator to check if user is authorized."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        username = f"@{user.username}" if user.username else None
        
        if not username:
            await update.message.reply_text(
                "You need to set a Telegram username to use this bot."
            )
            return
        
        if not csv_handler.is_authorized(username):
            await update.message.reply_text(
                "You are not authorized to use this bot. "
                "Please contact the administrator."
            )
            logger.warning(f"Unauthorized access attempt by {username}")
            return
        
        return await func(update, context)
    
    return wrapper


@is_authorized
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    username = f"@{user.username}"
    email = csv_handler.get_email(username)
    
    welcome_message = f"""
Welcome to the LiteLLM Management Bot!

Your authorized username: {username}

Available commands:
/create_token - Create a new access token for a user
/help - Show this help message

Examples:
/create_token
"""
    await update.message.reply_text(welcome_message)


@is_authorized
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_message = """
Available commands:

/create_token
Create a new access token for a user. Optionally specify models (comma-separated).
Examples:
  /create_token 

/help
Show this help message.
"""
    await update.message.reply_text(help_message)


@is_authorized
async def create_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /create_token command."""
    user = update.effective_user
    username = f"@{user.username}"
    email = csv_handler.get_email(username)
    email = email if email else f"{user.username}@nstu.ru"
    models = None


    if not litellm_client.user_exists(email):
        await update.message.reply_text(f"User with email: {email} does not exist. Creating...")
        user_creation_result = litellm_client.create_user(email,
                                                          team_name=DEFAULT_TEAM_NAME)
        await update.message.reply_text(f"Done!\n")

    active_tokens = litellm_client.get_active_tokens(email)
    if active_tokens.get("count") > 1:
        response = "You already have an access token."
        await update.message.reply_text(response, parse_mode='Markdown')

    else:
        await update.message.reply_text(f"Creating access token for: {email}...")
        result = litellm_client.create_token(email, models=models,
                                             duration=DEFAULT_TOKEN_DURATION,
                                             max_budget=DEFAULT_TOKEN_BUDGET)
    
        if result['success']:
            data = result['data']
            response = f"Access token created successfully!\n\n"

            if 'key' in data:
                response += f"Token: `{data['key']}`\n"
            elif 'token' in data:
                response += f"Token: `{data['token']}`\n"

            response += f"\nEmail: {email}\n"

            if models:
                response += f"Models: {', '.join(models)}\n"

            if 'expires' in data:
                response += f"Expires: {data['expires']}\n"

            response += "\nKeep this token secure!"

            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"Token created for {email} by {update.effective_user.username}")
        else:
            error_msg = f"Failed to create token.\n\nError: {result['error']}"
            if result.get('status_code'):
                error_msg += f"\nStatus Code: {result['status_code']}"
            await update.message.reply_text(error_msg)
            logger.error(f"Failed to create token for {email}: {result['error']}")


async def unauthorized_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages from unauthorized users."""
    user = update.effective_user
    username = f"@{user.username}" if user.username else "No username"
    
    if not user.username:
        await update.message.reply_text(
            "You need to set a Telegram username to use this bot."
        )
        return
    
    if not csv_handler.is_authorized(f"@{user.username}"):
        await update.message.reply_text(
            "You are not authorized to use this bot. "
            "Please contact the administrator."
        )
        logger.warning(f"Unauthorized message from {username}")


def main():
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("create_token", create_token_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unauthorized_message))
    
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
