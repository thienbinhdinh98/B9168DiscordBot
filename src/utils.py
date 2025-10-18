import functools
import time
from typing import Callable, Any
import logging
from discord.ext import commands

logger = logging.getLogger('discord')

def retry(max_retries: int = 5, backoff_factor: float = 2.0):
    """Decorator to retry a function multiple times"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    logger.debug(f"Attempt {attempt + 1}/{max_retries}")
                    result = func(*args, **kwargs)
                    
                    # If function returns None or False, retry
                    if result is not None:
                        return result
                        
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # Wait before retry
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
            
            logger.error(f"All {max_retries} attempts failed")
            return None
        return wrapper
    return decorator

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name='ping', description='Check bot latency')
    async def ping(self, ctx):
        """Check bot latency"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f'🏓 Pong! Latency: {latency}ms')
