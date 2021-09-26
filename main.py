from gevent import monkey
monkey.patch_socket()
import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from pymongo import MongoClient

# Set discord bot intents
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Load token and guild info from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

# Connect to MongoDB
client = MongoClient('localhost', 27017)
db = client['KinoBotDB']


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds)
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    # Load basic member info
    new_members = 0
    async for member in guild.fetch_members():
        cursor = db['Users']
        if cursor.find_one({'id': member.id}):
            break
        else:
            cursor.insert_many([{'id': member.id, 'member_name': member.name, 'display_name': member.display_name}])
            new_members += 1
    print(f'{new_members} new members since last connection!')


@bot.command(name='test')
async def test(ctx):
    await ctx.send(":tomato:")


bot.run(TOKEN)
