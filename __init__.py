import asyncio, sqlite3, os, psutil
from datetime import datetime
from discord.ext import commands
from hashlib import sha256
from env import env

bot = commands.Bot(command_prefix=env['COMMAND_PREFIX'])
bot.remove_command('help')

bot.db_connection = sqlite3.connect('nitro.db')
bot.db_connection.row_factory = sqlite3.Row
bot.db_connection.isolation_level = None

bot.uptime = datetime.utcnow()
bot.process = psutil.Process()
bot.cog_hashes = {}

@bot.event
async def on_ready():
    print('Ready!')

# Loading commands
cogs = [file.split('.')[0] for file in os.listdir('cogs') if file.endswith('py')]
for cog in cogs:
    bot.load_extension(f'cogs.{cog}')
    with open(f'cogs/{cog}.py', 'rb') as f:
        bot.cog_hashes[f'cogs.{cog}'] = sha256(f.read()).hexdigest()

bot.run(env['BOT_TOKEN'])
