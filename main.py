from get_token import get_token
import json
import asyncio
import discord
from Music import Music
from discord.ext import commands


intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='YAYAB',
    intents=intents
)


@bot.event
async def on_ready():
    #Loads in slash commands
    await bot.tree.sync()
    print(f'YAYAB Instance Started as {bot.user} (ID: {bot.user.id})')
    print('------')


async def main():
    async with bot:
        with open('config.json') as config:
            c = json.load(config)
            token = c['token']
        await bot.add_cog(Music(bot))
        await bot.start(token)


asyncio.run(main())