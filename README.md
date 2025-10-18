# Qidian Discord Bot

A Discord bot that monitors Chinese web novels from Qidian and automatically notifies you when new chapters are released. Features automatic translation of chapter titles to Vietnamese using OpenAI.

## Features

- 📚 **Subscribe to Qidian novels** - Track your favorite novels by URL
- 🔔 **Automatic notifications** - Get pinged when new chapters are released
- 🌐 **Vietnamese translation** - Chapter titles automatically translated using AI
- 📊 **Novel management** - List and view information about subscribed novels
- ⚡ **Slash commands** - Modern Discord slash command support
- 🐳 **Docker support** - Easy deployment with Docker and docker-compose

## Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/qidian_subscribe` | Subscribe to a Qidian novel | `/qidian_subscribe <url> [translated_title]` |
| `/qidian_list` | List all subscribed novels | `/qidian_list` |
| `/qidian_get_info` | Get detailed novel information | `/qidian_get_info <novel_name>` |
| `/ping` | Check bot latency | `/ping` |

## Prerequisites

- Python 3.12+
- Discord Bot Token
- OpenAI API Key
- Docker & Docker Compose (for containerized deployment)

## Installation

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/qidian-discord-bot.git
cd qidian-discord-bot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run the bot**
```bash
python bot.py
```

### Docker Deployment

1. **Clone and configure**
```bash
git clone https://github.com/yourusername/qidian-discord-bot.git
cd qidian-discord-bot
cp .env.example .env
# Edit .env with your credentials
```

2. **Set permissions**
```bash
sudo chown -R 1000:1000 data/ logs/
```

3. **Build and run**
```bash
docker-compose build
docker-compose up -d
```

4. **View logs**
```bash
docker-compose logs -f
```

## Configuration

Create a `.env` file in the project root:

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
NOTIFICATION_CHANNEL_ID=your_channel_id_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

### Getting Your Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the token
5. Enable "Message Content Intent" and "Server Members Intent"
6. Go to OAuth2 → URL Generator
7. Select scopes: `bot` and `applications.commands`
8. Select permissions: `Send Messages`, `Embed Links`, `Read Messages/View Channels`
9. Use the generated URL to invite your bot

### Getting Your Channel ID

1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click the channel where you want notifications
3. Click "Copy ID"

## Project Structure

```
qidian-discord-bot/
├── bot.py                  # Main bot entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── .env                   # Environment variables (create from .env.example)
├── .env.example           # Example environment file
├── .dockerignore          # Docker ignore patterns
├── cogs/
│   ├── __init__.py
│   └── Qidian.py          # Qidian novel tracking cog
├── utils.py               # Utility functions (retry decorator)
├── data/
│   └── qidian/
│       └── novel.json     # Subscribed novels database
└── logs/
    └── bot.log            # Application logs
```

## Usage Examples

### Subscribe to a novel
```
/qidian_subscribe https://www.qidian.com/book/1039994731/catalog/ Đại Đạo Chi Thượng
```

### List all subscribed novels
```
/qidian_list
```

### Get novel information
```
/qidian_get_info Đại Đạo Chi Thượng
```

## How It Works

1. **Novel Tracking**: The bot periodically checks (every 30 minutes) all subscribed novels for new chapters
2. **Chapter Detection**: Compares the latest chapter on Qidian with the stored local chapter
3. **Translation**: Uses OpenAI GPT to translate Chinese chapter titles to Vietnamese
4. **Notification**: Sends an embed message to the configured Discord channel with the new chapter information

## Docker Management

```bash
# Start the bot
docker-compose up -d

# Stop the bot
docker-compose down

# View logs
docker-compose logs -f

# Restart the bot
docker-compose restart

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Access container shell
docker-compose exec discord-bot /bin/bash
```

## Troubleshooting

### Bot not responding
- Check if the bot is online in Discord
- Verify `DISCORD_TOKEN` is correct
- Ensure Message Content Intent is enabled

### No notifications
- Verify `NOTIFICATION_CHANNEL_ID` is correct
- Check bot has permissions to send messages in the channel
- Check logs: `docker-compose logs -f`

### Permission errors in Docker
```bash
sudo chown -R 1000:1000 data/ logs/
docker-compose restart
```

### Translation not working
- Verify `OPENAI_API_KEY` is valid
- Check OpenAI API credits/quota
- Review logs for API errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) - Web scraping
- [OpenAI](https://openai.com/) - AI translation services
- [Qidian](https://www.qidian.com/) - Source of web novels

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/yourusername/qidian-discord-bot/issues).

## Disclaimer

This bot is for personal use and educational purposes. Please respect Qidian's terms of service and rate limits. The bot implements retry logic and exponential backoff to avoid excessive requests.