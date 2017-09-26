import asyncio, sqlite3, os
from discord.ext import commands
from env import env

bot = commands.Bot(command_prefix=env['COMMAND_PREFIX'])
bot.db_connection = sqlite3.connect(f'{env["PWD"]}/nitro.db')
bot.db_connection.row_factory = sqlite3.Row
bot.db_connection.isolation_level = None

@bot.event
async def on_ready():
    print('Ready!')

@bot.group(aliases=['ext', 'cog'], hidden=True)
@commands.check(lambda ctx: ctx.message.author.id == '136856172203474944')
async def extension():
    pass

@extension.command(pass_context=True, hidden=True)
@commands.check(lambda ctx: ctx.message.author.id == '136856172203474944')
async def reload(ctx, ext: str, use_prefix=True):
    ext = ('cogs.' if use_prefix else '') + ext

    try:
        bot.unload_extension(ext)
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        await bot.say('Failed to unload extension {}\n{}'.format(ext, exc))
        return

    try:
        bot.load_extension(ext)
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        await bot.say('Failed to load extension {}\n{}'.format(ext, exc))
        return

    await bot.add_reaction(ctx.message, '\U00002705')

# Loading commands
cogs = [file.split('.')[0] for file in os.listdir(f'{env["PWD"]}/cogs') if file.endswith('py')]
for cog in cogs:
    bot.load_extension(f'cogs.{cog}')

bot.run(env['BOT_TOKEN'])
