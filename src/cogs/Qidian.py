import discord
import os
from discord.ext import commands, tasks
from dotenv import load_dotenv
import logging
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from typing import Optional
from openai import OpenAI
from utils import retry
import time

load_dotenv()

client = OpenAI(
    api_key = os.environ.get("OPENAI_API_KEY"),
)

logger = logging.getLogger('discord')
BASE_DIR = Path(__file__).resolve().parent.parent  # Go up to project root
DATA_DIR = BASE_DIR / 'data' / 'qidian'
DATA_LOC = DATA_DIR / 'novel.json'
CHANNEL_ID = int(os.getenv('QIDIAN_NOTIFICATION_CHANNEL_ID', '0'))
qidian_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.qidian.com/',
}

@dataclass
class NovelInfo:
    url: str
    original_title: str | None = None
    translated_title: str | None = None
    last_chapter_title: str | None = None
    last_chapter_title_translated: str | None = None


class Qidian(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notification_channel_id = CHANNEL_ID
        self.check_novel_updates.start()

    def cog_unload(self):
        self.check_novel_updates.cancel()  # Stop loop when cog unloads

    def contain_duplicate(self, novels, novel_info):
        for novel in novels:
            if (novel['url'] == novel_info.url or 
                novel['original_title'] == novel_info.original_title
                or novel['translated_title'] == novel_info.translated_title):
                return True
        return False
    
    def get_novel(self, novel_name: str, option:str="N/A") -> NovelInfo | list[NovelInfo] | None:
        '''
        Load novel information from data/qidian/{novel_name}.json
        '''
        
        novels = []
        novel_info: NovelInfo = None
        if Path(DATA_LOC).exists():
            with open(DATA_LOC, 'r', encoding='utf-8') as f:
                try:
                    novels = json.load(f)
                except json.JSONDecodeError:
                    novels = []
            

        if option == "all":
            logger.info("Fetching all novels info")
            return novels

        logger.info(f"Looking for novel info with name: {novel_name}")  
        for novel in novels:
            original = (novel.get('original_title') or "").lower()
            translated = (novel.get('translated_title') or "").lower()
            
            if novel_name.lower() in original or novel_name.lower() in translated:
                novel_info = NovelInfo(**novel)  # Convert dict to NovelInfo here
                break

        if novel_info is None:
            return None
        return novel_info
    
    def get_chapter_title_translated(self, chapter_title: str) -> str:
        '''
        Use OpenAI to translate chapter title to English.
        '''
        if chapter_title == "N/A":
            return "N/A"
        
        try:
            system_prompt = """You are a translator specializing in Chinese web novels to Vietnamese. 
Use Sino-Vietnamese words for cultivation/literary terms while maintaining natural Vietnamese grammar.
Always format as "Chương {number}: {title}"."""
            user_prompt = f"Translate to Vietnamese: {chapter_title}"

            logger.info(f"Translating chapter title: {chapter_title} using OpenAI API")
            response = client.responses.create(
                model="gpt-5-nano",
                reasoning={"effort": "low"},
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            translation = response.output_text
            logger.info(f"Translated chapter title: {chapter_title} -> {translation}")
            return translation
        except Exception as e:
            logger.error(f"Error translating chapter title '{chapter_title}': {e}")
            return "N/A"
    
    @retry(max_retries=5, backoff_factor=2.0)
    async def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        '''
        Fetch the HTML content of the URL and return a BeautifulSoup object.
        '''
        try:
            response = requests.get(url, headers=qidian_headers, timeout=10)
            response.raise_for_status()  # Raises exception for 4xx/5xx
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {response.status_code} for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching {url}")  # Includes traceback
            return None
    
    def get_last_chapter(self, soup: BeautifulSoup) -> Optional[str]:
        '''
        Extract the last chapter title from the BeautifulSoup object.
        '''
        try:
            all_chapters = soup.find_all('li', attrs={'data-rid': True})
            if all_chapters:
                last_chapter = all_chapters[-1]
                chapter_title_tag = last_chapter.find('a')
                if chapter_title_tag:
                    return chapter_title_tag.text.strip()
            return "N/A"
        except Exception as e:
            logger.error(f"Error extracting last chapter: {e}")
            return "N/A"
    
    async def scrape_qidian_novel(self, url: str, translated_title:str) -> NovelInfo:
        '''
        Scrape the Qidian novel page to extract novel information.
        '''
        novel = NovelInfo(url=url, translated_title=translated_title)
        logger.info(f"Scraping Qidian novel: {url}")  # INFO instead of DEBUG
        
        try:
            soup = await self.get_soup(url)
            if not soup:
                return None
            
            book_name_tag = soup.find('em', id='bookName_only')

            # Extract chapter information if needed
            if book_name_tag:
                novel.original_title = book_name_tag.text.strip()
                logger.info(f"Found novel: {novel.original_title}")
                novel.last_chapter_title = self.get_last_chapter(soup)
                novel.last_chapter_title_translated = self.get_chapter_title_translated(novel.last_chapter_title)
            else:
                logger.warning(f"Could not find book name on page: {url}")
                
            return novel
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {response.status_code} for {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error scraping {url}")  # Includes traceback
            return None

    '''
    Fetch novel information from the provided Qidian URL and subscribe the user.
    '''
    async def get_and_subscribe(self, url: str, translated_title:str="N/a") -> NovelInfo:
        logger.info("Fetching novel information from Qidian...")
        novel_info = await self.scrape_qidian_novel(url, translated_title)
        logger.info("Done fetching novel information from Qidian...")
        
        if not novel_info:
            return None
        
        logger.debug(f"Fetched novel info: {novel_info}")
        Path(DATA_LOC).parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing novels
        novels = []
        if Path(DATA_LOC).exists():
            with open(DATA_LOC, 'r', encoding='utf-8') as f:
                try:
                    novels = json.load(f)
                except json.JSONDecodeError:
                    novels = []
        
        # Append new novel
        
        if not self.contain_duplicate(novels, novel_info):
            novels.append(asdict(novel_info))
        else:
            # Update existing novel
            for i, novel in enumerate(novels):
                if novel['original_title'] == novel_info.original_title:
                    novels[i] = asdict(novel_info)
                    break
        
        # Write back all novels
        with open(DATA_LOC, 'w', encoding='utf-8') as f:
            json.dump(novels, f, indent=4, ensure_ascii=False)

        return novel_info

    async def push_chapter_update(self, novel: dict | NovelInfo):
        """Send new chapter notification to Discord channel"""
        try:
            # Get the channel
            channel = self.bot.get_channel(self.notification_channel_id)
            
            if not channel:
                logger.error(f"Channel {self.notification_channel_id} not found!")
                return
            
            # Create embed for notification
            embed = discord.Embed(
                title="📖 New Chapter Update!",
                color=0x00ff00,  # Green
                timestamp=discord.utils.utcnow()
            )
            
            title = novel.get('translated_title') or novel.get('original_title', 'Unknown')
            embed.add_field(name="Novel", value=title, inline=False)
            
            original_chapter = novel.get('last_chapter_title', 'N/A')
            embed.add_field(name="📚 Chapter (Chinese)", value=f"`{original_chapter}`", inline=False)
            
            translated_chapter = novel.get('last_chapter_title_translated', 'N/A')
            if translated_chapter and translated_chapter != 'N/A':
                embed.add_field(name="🌐 Chapter (Vietnamese)", value=f"`{translated_chapter}`", inline=False)
            
            url = novel.get('url', '')
            if url:
                embed.add_field(name="🔗 Link", value=f"[Read on Qidian]({url})", inline=False)
            
            embed.set_footer(text="Qidian Update Checker")
            
            await channel.send(embed=embed)
            logger.info(f"✓ Notification sent for {title}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    @commands.hybrid_command(name='qidian_subscribe', description='Subscribe to a Qidian novel')
    async def qidian_subscribe(self, ctx, url:str, translated_title: str = "N/A"):
        novel_info: NovelInfo = None
        try:
            logger.debug(f"Subscribing to Qidian novel at URL: {url} with translated title: {translated_title}")
            novel_info = await self.get_and_subscribe(url, translated_title)
        except Exception as e:
            logger.error(f"Error in qidian_subscribe command: {e}")

        if novel_info: 
            logger.info(f"Subscribed to the novel '{novel_info.original_title}' from Qidian.")
            message = f"Subscribed to the novel '{url}' from Qidian."
        else:
            logger.info(f"Failed to subscribe to the novel from Qidian.")
            message = "Failed to subscribe to the novel."
        
        await ctx.send(message)

    @commands.hybrid_command(name='qidian_get_info', description='Get novel information')
    async def qidian_info(self, ctx, *, novel_name: str):
        # Place holder for fetching novel info from json file
        '''
        Load novel information from data/qidian/{novel_name}.json
        '''
        novel_info: NovelInfo = self.get_novel(novel_name)

        if novel_info is None:
            await ctx.send(f"❌ Novel not found: \"{novel_name}\"\nUse `!qidian_list` to see all subscribed novels.")
            return
        
        embed = discord.Embed(
            title=novel_info.translated_title or novel_info.original_title,
            description=novel_info.original_title if novel_info.translated_title else "",
            color=discord.Color.blue(),
            url=novel_info.url
        )

        embed.add_field(
            name="📖 Last Chapter",
            value=novel_info.last_chapter_title or "N/A",
            inline=False
        )

        if novel_info.last_chapter_title_translated and novel_info.last_chapter_title_translated != "N/A":
            embed.add_field(
                name="🌐 Translation",
                value=novel_info.last_chapter_title_translated,
                inline=False
            )

        embed.add_field(
            name="🔗 Link",
            value=f"[Read on Qidian]({novel_info.url})",
            inline=False
        )

        embed.set_footer(text="Qidian Novel Info")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='qidian_list', description='List all subscribed novels')
    async def fetch_novel_info(self, ctx):
        novels = self.get_novel("", option="all")
        
        if not novels:
            await ctx.send("❌ No subscribed novels found.")
            return
        
        embed = discord.Embed(
            title="📚 Subscribed Qidian Novels",
            description="Here are the novels you have subscribed to:",
            color=discord.Color.green()
        )

        for novel in novels:
            title = novel.get('translated_title') or novel.get('original_title')
            url = novel.get('url')
            last_chapter =  novel.get('last_chapter_title') if novel.get('last_chapter_title_translated') == "N/A" else novel.get('last_chapter_title_translated')
            embed.add_field(
                name=title,
                value=f"{last_chapter}\n[Read on Qidian]({url})",
                inline=False
            )

        embed.set_footer(text="Qidian Subscribed Novels")

        await ctx.send(embed=embed)

    @tasks.loop(minutes=5)
    async def check_novel_updates(self):
        '''
        Periodically check for updates on all subscribed novels.
        '''
        novels = self.get_novel("", option="all")
        if not novels:
            logger.info("No subscribed novels to check for updates.")
            return
        
        for novel in novels:
            url = novel.get('url')
            local_last_chapter = novel.get('last_chapter_title') or "N/A"
            remote_last_chapter = self.get_last_chapter(await self.get_soup(url))
            new_chapter_found = remote_last_chapter != local_last_chapter
            logger.info(f"Checking novel: {novel.get('original_title')} | Local: {local_last_chapter} | Remote: {remote_last_chapter} | New Chapter: {new_chapter_found}")
            if new_chapter_found:
                logger.info(f"New chapter detected for {novel.get('translated_title')}: {remote_last_chapter}")
                last_chapter_title_translated = self.get_chapter_title_translated(remote_last_chapter)
                novel['last_chapter_title'] = remote_last_chapter
                novel['last_chapter_title_translated'] = last_chapter_title_translated
                logger.info(f"Updated local record for {novel.get('translated_title') or novel.get('original_title')}")
                # Push notification to Discord channel for new chapter
                await self.push_chapter_update(novel)
            time.sleep(10)  # To avoid hitting rate limits

            
        # Write back all novels after checking updates
        with open(DATA_LOC, 'w', encoding='utf-8') as f:
            json.dump(novels, f, indent=4, ensure_ascii=False)   

    @check_novel_updates.before_loop
    async def before_check_novel_updates(self):
        await self.bot.wait_until_ready()