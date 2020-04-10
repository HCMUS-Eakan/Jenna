import discord
import typing
import re
import aiohttp
import colors
import math
import random
import cogs
import env
import const
import io

from .core import converter as conv
from .core import embed_limit
from .core.emotes import external, utils
from discord.ext import commands

EMOTES_PER_PAGE = 25
EMOJI_PATTERN = '(:[^:\s]+:)(?!\d)'
REAL_EMOJI_PATTERN = '(<a*:[^:\s]+:\d+>)'
HOME_GUILD = 596171359747440657

EMBED_BACKCOLOR = 0x2f3136

TWEMOJI_CDN = 'https://twemoji.maxcdn.com/v/latest/72x72/%s.png'

EXTERNAL_EMOJIS = 'external_emojis'

class Emotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.external_emojis = {}
        self.external_paginator = external.EmojiPaginator(self)
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.Persist = self.bot.get_cog(cogs.PERSIST)
        await self.Persist.wait_until_loaded()
        self.external_emojis = self.Persist.get(EXTERNAL_EMOJIS, {})
        self.Persist.set(EXTERNAL_EMOJIS, self.external_emojis)

    @commands.command(aliases=['big'])
    async def enlarge(self, context, emoji:conv.NitroEmoji):
        embed = discord.Embed(color=EMBED_BACKCOLOR)
        url = None
        name = emoji
        ext = 'png'
        if type(emoji) in [discord.Emoji, discord.PartialEmoji]:
            file = await emoji.url.read()
            name = emoji.name
            if emoji.animated:
                ext = 'gif'
        else:
            url = TWEMOJI_CDN % '-'.join(format(ord(char), 'x') for char in emoji)
            file = await utils.download(url)
            if not file:
                url = TWEMOJI_CDN % format(ord(emoji[0]), 'x')
                file = await utils.download(url)
        
        if file:
            file = discord.File(io.BytesIO(file), filename=f'{name}.{ext}')
            await context.send(file=file)
        else:
            await context.message.add_reaction('⁉️')

    @commands.command(aliases=['emojis'])
    async def emotes(self, context, page:int=1):
        home_guild = self.bot.get_guild(HOME_GUILD)
        embed = colors.embed()
        embed.set_author(name='Available Emotes')
        total_page = math.ceil(len(home_guild.emojis) / EMOTES_PER_PAGE)
        embed.set_footer(text=f'Page {page}/{total_page}')
        
        all_emojis = sorted(home_guild.emojis, key=lambda e: e.name)
        emojis = []
        start = EMOTES_PER_PAGE * (page - 1)
        end = EMOTES_PER_PAGE * page
        page_emojis = all_emojis[start:end]
        for e in page_emojis:
            emojis += [f'{e} `:{e.name}:`']
        embed.description = '\n'.join(emojis)
        await context.send(embed=embed)
    
    @commands.command(aliases=['nitrojis'])
    async def nitrotes(self, context, page=1):
        await context.trigger_typing()
        embed = await self.external_paginator.get_page(context, page)
        await context.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def drop(self, context, emoji:conv.NitroEmoji, author:typing.Optional[conv.Member], i:int=1):
        counter = 1
        async for message in context.history(limit=None, before=context.message):
            if author and message.author != author:
                continue
            if counter < i:
                counter += 1
                continue
            break
        await message.add_reaction(emoji)
        
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author == self.bot.user: return
        context = await self.bot.get_context(msg)
        if context.command:
            return
        await self.cache_external_emojis(msg)
        if env.TESTING: return
        await self.reply_emojis(msg)
    
    def get_emoji(self, name):
        return discord.utils.get(self.bot.emojis, name=name)

    async def reply_emojis(self, msg):
        context = await self.bot.get_context(msg)
        match = re.findall(EMOJI_PATTERN, msg.content)
        emojis = []
        externals = []

        for emoji in match:
            name = emoji.replace(':', '')
            emoji = self.get_emoji(name)
            if not emoji:
                external = self.external_emojis.get(name)
                external = await utils.to_partial_emoji(context, external)
                emoji = await self.add_emoji(external.name, await external.url.read())
                externals += [emoji]
            
            if emoji:
                emojis += [str(emoji)]
        
        if emojis:
            emojis = ''.join(emojis)
            await msg.channel.send(emojis)
        
        for e in externals:
            await e.delete()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        emoji = reaction.emoji
        if isinstance(emoji, discord.PartialEmoji):
            self.external_emojis[emoji.name] = str(emoji)

    async def cache_external_emojis(self, msg):
        context = await self.bot.get_context(msg)
        emojis = re.findall(REAL_EMOJI_PATTERN, msg.content)
        if msg.embeds:
            embed = msg.embeds[0]
            emojis += re.findall(REAL_EMOJI_PATTERN, embed.description or '')
            for f in embed.fields:
                emojis += re.findall(REAL_EMOJI_PATTERN, f.name)
                emojis += re.findall(REAL_EMOJI_PATTERN, f.value)
        emojis += [r.emoji for r in msg.reactions if isinstance(r.emoji, discord.PartialEmoji)]
        
        for e in emojis:
            partial = await utils.to_partial_emoji(context, e) if isinstance(e, str) else e
            known = self.get_emoji(partial.name)
            cached = self.external_emojis.get(partial.name)
            should_cache = not (known or cached)
            if should_cache:
                self.external_emojis[partial.name] = str(e)
    
    @commands.group(aliases=['emoji'], hidden=True)
    async def emote(self, context):
        pass

    @emote.command()
    @commands.is_owner()
    async def scan(self, context, channel:typing.Union[discord.TextChannel, int]=None, limit:int=None):
        if isinstance(channel, int):
            channel = self.bot.get_channel(channel)
        channel = channel or context.channel
        async with context.typing():
            async for message in channel.history(limit=limit):
                contains_emojis = re.findall(REAL_EMOJI_PATTERN, message.content)
                if contains_emojis:
                    await self.cache_external_emojis(message)
        await context.message.add_reaction('✅')

    @emote.command()
    @commands.is_owner()
    async def add(self, context, url, name=None):
        response = '⁉️'
        home_guild = self.bot.get_guild(HOME_GUILD)

        async with context.typing():
            image = await download_image(url)
            if image:
                if not name:
                    name = 'emoji%04d' % random.randint(0, 9999)
                await home_guild.create_custom_emoji(name=name, image=image)
                response = self.get_emoji(name)
            await context.message.add_reaction(response)
    
    async def add_emoji(self, name, image):
        return await self.bot.get_guild(HOME_GUILD).create_custom_emoji(name=name, image=image)

async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                return await r.read()

def setup(bot):
    bot.add_cog(Emotes(bot))