from discord.ext import commands
from hashlib import sha256
from subprocess import call
from io import StringIO
import discord, asyncio, functools, sys


class Admin:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True, pass_context=True)
    @commands.check(lambda ctx: ctx.message.author.id == '136856172203474944')
    async def update(self, ctx):
        await self.bot.send_typing(ctx.message.channel)
        await self.bot.loop.run_in_executor(None, functools.partial(call, 'git pull origin master', shell=True))

    @commands.command(hidden=True)
    @commands.check(lambda ctx: ctx.message.author.id == '136856172203474944')
    async def reboot(self):
        await self.bot.say('Goodbye')
        await self.bot.logout()

    @commands.group(hidden=True, aliases=['ext', 'cog'])
    @commands.check(lambda ctx: ctx.message.author.id == '136856172203474944')
    async def extension(self):
        pass

    @extension.command()
    async def load(self, ext, use_prefix=True):
        ext = ('cogs.' if use_prefix else '') + ext

        if not await self._load_extension(ext):
            return

        await bot.add_reaction(ctx.message, '\U00002705')

    @extension.command()
    async def unload(self, ext, use_prefix=True):
        ext = ('cogs.' if use_prefix else '') + ext

        if not await self._unload_extension(ext):
            return

        await bot.add_reaction(ctx.message, '\U00002705')

    @extension.command()
    async def refresh(self):
        reloaded = []
        errored = []

        for cog, hash in self.bot.cog_hashes.items():
            new_hash = Admin._hash_file(f'{cog.replace(".", "/")}.py')

            # Checking if the saved hash and new hash are different (Files are different)
            if hash != new_hash:
                if await self._unload_extension(cog) and await self._load_extension(cog):
                    reloaded.append(cog)
                else:
                    errored.append(cog)

        e = discord.Embed()
        e.add_field(name='Reloaded Cogs', value='\n'.join(reloaded if reloaded else ['Nothing']), inline=False)
        e.add_field(name='Errored Cogs', value='\n'.join(errored if errored else ['Nothing']), inline=False)
        await self.bot.say(None, embed=e)

    @extension.command()
    async def reload(self, ext, use_prefix=True):
        ext = ('cogs.' if use_prefix else '') + ext

        if await self._unload_extension(ext) and await self._load_extension(ext):
            await bot.add_reaction(ctx.message, '\U00002705')

    async def _unload_extension(self, ext):
        try:
            self.bot.unload_extension(ext)
        except Exception as e:
            exc = f'{type(e).__name__}: {e}'
            await self.bot.say(f'Failed to unload extension {ext}\n{exc}')
            return False

        del self.bot.cog_hashes[ext]
        return True

    async def _load_extension(self, ext):
        try:
            self.bot.load_extension(ext)
        except Exception as e:
            exc = f'{type(e).__name__}: {e}'
            await self.bot.say(f'Failed to load extension {ext}\n{exc}')
            return False

        self.bot.cog_hashes[ext] = Admin._hash_file(f'{ext.replace(".", "/")}.py')

        return True

    @staticmethod
    def _hash_file(filename):
        with open(filename, 'rb') as f:
            return sha256(f.read()).hexdigest()


def setup(bot):
    bot.add_cog(Admin(bot))
