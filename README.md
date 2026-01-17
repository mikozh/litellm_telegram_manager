# LiteLLM Telegram Bot

A Telegram bot for managing LiteLLM users and access tokens. The bot allows authorized users to create LiteLLM users and generate access tokens through simple Telegram commands.

## Features

- **User Authorization**: Only users listed in a CSV file can interact with the bot
- **User Management**: Create new users in LiteLLM with email addresses
- **Token Generation**: Generate access tokens for users with optional model restrictions
- **CSV-based Access Control**: Easy to add or remove authorized users by editing a CSV file
- **Secure**: All operations require authorization and use the LiteLLM master key

## Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- A running LiteLLM server with API access
- LiteLLM master key for API authentication

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mikozh/litellm_telegram_api.git
cd litellm_telegram_api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Edit the `.env` file with your configuration:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
LITELLM_API_URL=http://localhost:4000
LITELLM_MASTER_KEY=your_litellm_master_key_here
USERS_CSV_PATH=users.csv
```

5. Create a `users.csv` file from the example:
```bash
cp users.csv.example users.csv
```

6. Edit `users.csv` to add authorized users:
```csv
telegram_username,email
@john_doe,john.doe@example.com
@jane_smith,jane.smith@example.com
```

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `LITELLM_API_URL`: URL of your LiteLLM server (e.g., `http://localhost:4000`)
- `LITELLM_MASTER_KEY`: Master key for LiteLLM API authentication
- `USERS_CSV_PATH`: Path to the CSV file containing authorized users (default: `users.csv`)

### CSV File Format

The `users.csv` file should have the following format:

```csv
telegram_username,email
@username1,user1@example.com
@username2,user2@example.com
```

- `telegram_username`: Telegram username with @ prefix
- `email`: Email address associated with the user

## Usage

### Starting the Bot

Run the bot with:
```bash
python bot.py
```

The bot will start and listen for commands from authorized users.

### Available Commands

#### `/start`
Shows a welcome message and lists all available commands.

#### `/help`
Displays detailed help information about all commands.

#### `/create_user <email>`
Creates a new user in LiteLLM with the specified email address.

**Example:**
```
/create_user john@example.com
```

#### `/create_token <email> [models]`
Creates a new access token for a user. Optionally specify allowed models as a comma-separated list.

**Examples:**
```
/create_token john@example.com
/create_token john@example.com gpt-4,gpt-3.5-turbo
```

#### `/reload`
Reloads the list of authorized users from the CSV file. Useful when you've added or removed users without restarting the bot.

## Security Considerations

1. **Keep your `.env` file secure**: Never commit it to version control
2. **Protect your master key**: The LiteLLM master key has full access to your LiteLLM instance
3. **Secure your CSV file**: Only authorized personnel should be able to modify the users.csv file
4. **Use HTTPS**: If your LiteLLM server is remote, ensure you're using HTTPS
5. **Monitor bot usage**: Check logs regularly for unauthorized access attempts

## Project Structure

```
litellm_telegram_api/
├── bot.py                 # Main bot application
├── csv_handler.py         # CSV file handling and user authorization
├── litellm_client.py      # LiteLLM API client
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment configuration
├── .gitignore            # Git ignore rules
├── users.csv.example     # Example authorized users file
└── README.md             # This file
```

## Troubleshooting

### Bot doesn't respond
- Check that the bot is running
- Verify your Telegram username is in the `users.csv` file with @ prefix
- Ensure you have a Telegram username set in your profile

### "You are not authorized" message
- Verify your username is correctly listed in `users.csv`
- Make sure the username includes the @ prefix
- Try running `/reload` if you just added yourself to the CSV

### API errors
- Verify your LiteLLM server is running and accessible
- Check that the `LITELLM_API_URL` is correct
- Ensure your `LITELLM_MASTER_KEY` is valid
- Check LiteLLM server logs for more details

### CSV file not found
- Ensure `users.csv` exists in the same directory as `bot.py`
- Check the `USERS_CSV_PATH` environment variable

## Development

### Running in Development Mode

For development, you can use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

### Running as a service

Copy `telelite.service` to `/etc/systemd/system/`

```commandline
sudo cp telelite.service /etc/systemd/system/
```

Start and enable the service

```commandline
systemctl daemon-reload
systemctl enable telelite.service
systemctl start telelite.service
systemctl status telelite.service
```

### Adding New Features

The bot is modular and easy to extend:

- **CSV Handler** (`csv_handler.py`): Manages user authorization
- **LiteLLM Client** (`litellm_client.py`): Handles API communication
- **Bot** (`bot.py`): Telegram bot logic and command handlers

## License

This project is provided as-is for use with LiteLLM.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review LiteLLM documentation: https://docs.litellm.ai/
3. Check bot logs for error messages

## Contributing

Contributions are welcome! Please ensure your code follows the existing style and includes appropriate error handling.
