import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
import logging
from pathlib import Path
from utils import Utils

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'bot.log'

# Ensure logs directory exists
LOG_DIR.mkdir(exist_ok=True)

# Setup logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# File handler (append mode to keep history)
file_handler = logging.FileHandler(
    filename=LOG_FILE, 
    encoding='utf-8', 
    mode='a'  # Append instead of overwrite
)
file_handler.setFormatter(logging.Formatter(
    '[{asctime}] [{levelname:<8}] {name}: {message}',
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{'
))

# Console handler (see logs in terminal)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '[{levelname:<8}] {name}: {message}',
    style='{'
))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load cogs
        from cogs.Qidian import Qidian
        await self.add_cog(Qidian(self))
        await self.add_cog(Utils(self))
        logger.info("Loaded Qidian cog")

bot = MyBot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Bot connected as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Bot is in {len(bot.guilds)} server(s)')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author.bot:
        return
    
    # Process commands
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return  # Silently ignore unknown commands
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    else:
        logger.error(f"Error in command {ctx.command}: {error}", exc_info=error)
        await ctx.send(f"❌ An error occurred: {str(error)}")

if __name__ == '__main__':
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)