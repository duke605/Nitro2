from discord.ext import commands
from hashlib import sha256
from subprocess import call
from io import StringIO
from racer import Racer
from util import choices, Arguments, nt_name_for_discord_id
from env import env
import discord, asyncio, functools, sys, inspect


class Admin:

    def __init__(self, bot):
        self.bot = bot
        self.con = bot.db_connection

    @commands.command(hidden=True, pass_context=True)
    @commands.check(lambda ctx: ctx.message.author.id == '136856172203474944')
    async def update(self, ctx):
        await self.bot.send_typing(ctx.message.channel)
        await self.bot.loop.run_in_executor(None, functools.partial(call, 'git pull origin master', shell=True))
        await self.bot.add_reaction(ctx.message, '\U00002705')

    @commands.command(hidden=True)
    @commands.check(lambda ctx: ctx.message.author.id == '136856172203474944')
    async def reboot(self):
        await self.bot.say('Goodbye')
        await self.bot.logout()

    @commands.group(hidden=True)
    @commands.check(lambda ctx: ctx.message.author.id == '136856172203474944')
    async def sudo(self):
        pass

    @sudo.command(pass_context=True, name='eval')
    async def _eval(self, ctx, *, code):

        """Evaluates code."""
        python = '```py\n' \
                 '# Input\n' \
                 '{}\n\n' \
                 '# Output\n' \
                 '{}' \
                 '```'

        _env = {
            'bot': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'server': ctx.message.server,
            'channel': ctx.message.channel,
            'author': ctx.message.author
        }

        _env.update(globals())

        await self.bot.send_typing(ctx.message.channel)

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await self.bot.say(python.format(code, type(e).__name__ + ': ' + str(e)))
            return

        await self.bot.say(python.format(code, result or 'N/A'))

    @sudo.command(pass_context=True, aliases=['reg'])
    async def register(self, ctx, *, msg):
        parser = Arguments(allow_abbrev=True, prog='sudo register')
        parser.add_argument('user', type=choices.user(ctx.message.server), help='The Discord user you wish to associate a Nitro Type account to.')
        parser.add_argument('username', help='The Nitro Type account you with to associate the Discord account with.')

        await self.bot.send_typing(ctx.message.channel)
        args = await parser.do_parse(self.bot, msg)

        if not args:
            return

        c = self.con.cursor()
        c.execute('SELECT * FROM users WHERE id = ? OR nitro_name LIKE ? LIMIT 1', (args.user.id, args.username))
        u = c.fetchone()

        if u:
            if u['id'] == args.user.id:
                await self.bot.say('That user already has a Nitro Type account associated with their Discord account.')
            elif u['nitro_name'].lower() == args.username.lower():
                await self.bot.say('That Nitro Type account is already associated to another\'s Discord account.')
            return

        racer = await Racer.get(args.username)
        if not racer:
            await self.bot.say(f'A Nitro Type account with the user name **{args.username}** does not exist.')
            return

        self.con.execute('INSERT INTO users VALUES (?, ?)', (args.user.id, racer.username))
        await self.bot.add_reaction(ctx.message, '\U00002705')
        await racer.apply_roles(self.bot, args.user)

    @sudo.command(pass_context=True, aliases=['unreg'])
    async def unregister(self, ctx, *, msg):
        parser = Arguments(allow_abbrev=True, prog='sudo register')
        parser.add_argument('user', type=choices.user(ctx.message.server), help='The Discord user you wish to unlink a Nitro Type account from.')

        await self.bot.send_typing(ctx.message.channel)
        args = await parser.do_parse(self.bot, msg)

        if not args:
            return

        nitro_name = nt_name_for_discord_id(args.user.id, self.con)
        if not nitro_name:
            await self.bot.say('That user does not have a Nitro Type account associated with their Discord account.')
            return

        self.con.execute('DELETE FROM users WHERE id = ?', (args.user.id,))
        await self.bot.add_reaction(ctx.message, '\U00002705')
        await self.bot.replace_roles(args.user, *list(filter(lambda r: r.name not in env['ROLE_NAMES'], args.user.roles)))

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
