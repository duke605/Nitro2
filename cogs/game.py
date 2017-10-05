from discord.ext import commands
from util import Arguments, choices, nt_name_for_discord_id, upload_to_imgur
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from racer import Racer
from team import Team
from car import Car
from collections import namedtuple
from env import env
import matplotlib

matplotlib.use('Agg')
import functools, discord, asyncio, traceback, sys, matplotlib.pyplot as plt, random

class Game:

    Verification = namedtuple('Verification', ['racer', 'car', 'expiry'])

    def __init__(self, bot):
        self.bot = bot
        self.con = bot.db_connection
        self.pending_registrations = {}

    async def on_command_error(self, ex, ctx):
        if type(ex) is commands.errors.CommandNotFound:
            return

        # Notfying the user that the command they used is on cooldown and then deleting the command
        if type(ex) is commands.errors.CommandOnCooldown:
            await self.bot.add_reaction(ctx.message, '\U0000231b')
            await asyncio.sleep(3)
            await self.bot.delete_message(ctx.message)
            return

        with StringIO() as out:
            traceback.print_exception(type(ex), ex, ex.__traceback__, file=out)
            out.seek(0)
            error = out.read()

        e = discord.Embed(colour=0xff0000)
        e.description = f'```{error}```'
        e.add_field(name='Command Input', value=ctx.message.content)
        e.add_field(name='Command User', value=ctx.message.author.mention)
        e.add_field(name='Command Channel', value=ctx.message.channel.mention)

        if ctx.message.server.id == '223233024127533056':
            await self.bot.send_message(self.bot.get_channel('361729723555905538'), None, embed=e)
        else:
            print(error)


    @commands.command(pass_context=True, description='Unassociates your Discord account with a NitroType account.')
    async def unregister(self, ctx):
        """
        {
            "usage": "unregister"
        }
        """

        author = ctx.message.author
        nt_name = nt_name_for_discord_id(author.id, self.con)
        if not nt_name:
            await self.bot.say('You do not have a NitroType account associated with your Discord account.')
            return

        self.con.execute('DELETE FROM users WHERE id = ?', (ctx.message.author.id,))
        await self.bot.add_reaction(ctx.message, '\U00002705')


        await self.bot.replace_roles(author, *list(filter(lambda r: r.name not in env['ROLE_NAMES'], author.roles)))

    @commands.command(pass_context=True, aliases=['reg'], description='Associates your Discord account with a NitroType account.')
    async def register(self, ctx, *, msg):
        """
        {
            "usage": "register username",
            "arguments": [
                {
                    "name": "username",
                    "type": "string",
                    "value": "The username (not display name) of the Nitro Type account you wish to associate with your Discord account."
                }
            ]
        }
        """

        author = ctx.message.author
        c = self.con.cursor()

        await self.bot.send_typing(ctx.message.channel)
        c.execute('SELECT * FROM users WHERE id = ? OR nitro_name LIKE ? LIMIT 1', (author.id, msg))
        u = c.fetchone()

        # Checking if the discord account is already registered
        if u:
            if u['id'] == ctx.message.author.id:
                await self.bot.say('A NitroType account is already associated with your Discord account.')
            elif u['nitro_name'] == msg:
                await self.bot.say('That NitroType account is already associated with someone else\'s Discord account.')
            else:
                await self.bot.say('A NitroType account is already associated with your Discord account.')

            return

        # Checking if the NT account exists
        racer = await Racer.get(msg)
        if not racer:
            await self.bot.say('A NitroType user with that name does not exist.')
            return

        # Checking if player has enough cars to be verified
        if len([c for c in racer.cars if c.owned]) <= 2:
            await self.bot.say('You must have more than 2 cars to be able to register.')
            return

        # Checking if they have a verification in the DB
        v = self.pending_registrations.get(ctx.message.author.id)

        if v and v.expiry >= datetime.utcnow():
            await self.bot.say('You already have a pending registration. Please type `!verify` to complete your registration.')
            return

        # Checking if there is an open registration on that user already
        if [1 for ver in self.pending_registrations.values() if ver.racer.username.lower() == msg.lower() and ver.expiry >= datetime.utcnow()]:
            await self.bot.say('There is already a pending registration for that NitroType account.')
            return

        await racer.update()
        cars = list(filter(lambda c: c.owned and c.id != racer.car.id, racer.cars))
        v_car = random.choice(cars)

        expiry = datetime.utcnow() + timedelta(minutes=2)
        self.pending_registrations[ctx.message.author.id] = Game.Verification(racer, v_car, expiry)

        e = discord.Embed()
        e.set_author(name=ctx.message.author.display_name, icon_url=author.avatar_url or author.default_avatar_url)
        e.description = f'To verify you are the owner of that account please change your vehicle to the **{v_car.name}**. Once you have changed your vehicle type `!verify`'
        e.set_thumbnail(url=v_car.thumbnail)
        await self.bot.say(None, embed=e)

    @commands.command(pass_context=True, description='Verifies your account. This command is to be used AFTER the register command.')
    async def verify(self, ctx):
        """
        {
            "usage": "verify"
        }
        """

        author = ctx.message.author
        v = self.pending_registrations.get(author.id)

        if not v or v.expiry < datetime.utcnow():
            await self.bot.say('You do not have a pending registration or your registration expired.')
            return

        racer = v.racer
        await racer.update()
        if racer.car.id == v.car.id:
            self.con.execute('INSERT INTO users VALUES (?, ?)', (author.id, racer.username))
            del self.pending_registrations[ctx.message.author.id]
            await self.bot.add_reaction(ctx.message, '\U00002705')
            await racer.apply_roles(self.bot, author)
            return

        e = discord.Embed()
        e.set_author(name=ctx.message.author.display_name, icon_url=author.avatar_url or author.default_avatar_url)
        e.description = f'To verify you are the owner of that account please change your vehicle to the **{v.car.name}**. Once you have changed your vehicle type `!verify`'
        e.set_thumbnail(url=v.car.thumbnail)
        await self.bot.say(None, embed=e)

    @commands.command(pass_context=True, aliases=['profile'], description="Shows a information about a racer's racer card.")
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def racer(self, ctx, *, msg=''):
        """
        {
            "usage": "racer [user]",
            "cooldown": 30,
            "arguments": [
                {
                    "name": "user",
                    "type": "mention | int",
                    "value": "The user you wish to get a racer card for. If omitted racer information with be retrieved for command user."
                }
            ]
        }
        """

        parser = Arguments(allow_abbrev=True, prog='racer')
        parser.add_argument('user', type=choices.nt_user(ctx.message.server), default=ctx.message.author, nargs='?')

        await self.bot.send_typing(ctx.message.channel)
        args = await parser.do_parse(self.bot, msg)

        if not args:
            return

        try:
            racer = await self._get_racer(args.user)
        except Exception as e:
            await self.bot.say(str(e))
            return

        e = racer.setup_embed()
        e.add_field(name='Current Car', value=f"{racer.car.name}", inline=False)
        e.add_field(name='Money', value=f"${racer.money:,}")
        e.add_field(name='Nitros Owned', value=f"{racer.nitros:,}")
        e.add_field(name='Level', value=racer.level)
        e.add_field(name='Profile Views', value=f'{racer.profile_views:,}')
        await self.bot.say(None, embed=e)

    @commands.command(pass_context=True, description='Shows statistical information about a racer')
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def stats(self, ctx, *, msg=''):
        """
        {
            "usage": "stats [user]",
            "cooldown": 30,
            "arguments": [
                {
                    "name": "user",
                    "type": "mention | int",
                    "value": "The user you wish to get stats for. If omitted stats information with be retrieved for command user."
                }
            ]
        }
        """

        parser = Arguments(allow_abbrev=True, prog='stats')
        parser.add_argument('user', type=choices.nt_user(ctx.message.server), default=ctx.message.author, nargs='?')

        await self.bot.send_typing(ctx.message.channel)
        args = await parser.do_parse(self.bot, msg)

        if not args:
            return

        try:
            racer = await self._get_racer(args.user)
        except Exception as e:
            await self.bot.say(str(e))
            return

        e = racer.setup_embed()
        e.add_field(name='Member Since', value=racer.created_at.strftime('%b %d, %Y at %I:%M %p').replace(' 0', ' '))
        e.add_field(name='Avg Speed', value=f'{racer.avg_speed:,} WPM')
        e.add_field(name='Highest Speed', value=f'{racer.highest_speed:,} WPM')
        e.add_field(name='Longest Session', value=f'{racer.longest_session:,}')
        e.add_field(name='Races Played', value=f'{racer.total_races:,}')
        e.add_field(name='Nitros Used', value=f'{racer.nitros_used:,}')
        e.add_field(name='Money', value=f'**Earned: **${racer.money_earned:,}\n**Spent: **${racer.money_spent:,}')
        e.add_field(name='Medals', value=f'\U0001f947 x{racer.medals_gold:,}\n\U0001f948 x{racer.medals_silver:,}\n\U0001f949 x{racer.medals_bronze:,}')
        racer.board_daily.add_field(e)
        racer.board_weekly.add_field(e)
        racer.board_monthly.add_field(e)
        racer.board_season.add_field(e)

        # Creating the racing log graph
        fig = plt.figure()
        count = len(racer.races)
        medals = fig.add_subplot(111, facecolor='#00000000', xticklabels=[''] * count, yticklabels=[''] * count, frameon=None)
        line = fig.add_subplot(111, facecolor='#00000000', xticklabels=[''] * count, yticklabels=[''] * count, frameon=None)

        for i, race in enumerate(racer.races):
            medals.scatter(i, race.wpm, color=race.medal_colour)

        line.plot(range(count), [race.wpm for race in racer.races], zorder=0)
        fig.subplots_adjust(bottom=0.38, top=0.61, right=1, left=0)

        with BytesIO() as buf:
            plt.savefig(buf, bbox_inches='tight', facecolor='#00000000', format='PNG')
            plt.close()
            link = await upload_to_imgur(buf)

            if link:
                e.set_image(url=link)

        await self.bot.say(None, embed=e)

    @commands.command(pass_context=True, description='Shows information about a NitroType team.')
    @commands.cooldown(1, 30, commands.cooldowns.BucketType.user)
    async def team(self, ctx, *, msg):
        """
        {
            "usage": "team tag",
            "cooldown": 30,
            "arguments": [
                {
                    "name": "tag",
                    "type": "string",
                    "value": "The tag of the team you wish to retrieve information for."
                }
            ]
        }
        """
        parser = Arguments(allow_abbrev=True, prog='stats')
        parser.add_argument('tag', help='Does stuff')

        await self.bot.send_typing(ctx.message.channel)
        args = await parser.do_parse(self.bot, msg)

        if not args:
            return

        t = await Team.get(args.tag)

        if not t:
            await self.bot.say('A Nitro Type team with that tag does not exist.')
            return

        founded_on = t.created_at.strftime('%b %d, %Y').replace(' 0', ' ')

        e = discord.Embed(colour=t.tag_colour)
        e.description = u'\u200B' if not t.other_requirements else t.other_requirements
        e.set_author(name=t.display_name, url=t.url, icon_url='')
        e.add_field(name='Enrollment', value=f'{t.enrollment.capitalize()}\n**Speed: **{t.min_speed}\n**Level: **{t.min_level}')
        e.add_field(name='About', value=f'**Founded On: **{founded_on}\n**Captain: **{t.captain_display_name or t.captain_username}\n**Member Count: **{t.member_count}')
        t.board_season.add_field(e)
        t.board_daily.add_field(e)
        t.board_weekly.add_field(e)
        t.board_monthly.add_field(e)
        await self.bot.say(None, embed=e)

    async def _get_racer(self, o):
        nt_name = o

        if isinstance(o, discord.User):
            nt_name = nt_name_for_discord_id(o.id, self.con)

            if not nt_name:
                raise Exception('User does not have a NitroType account associated with their Discord account.')

        racer = await Racer.get(nt_name)

        if not racer:
            if type(o) is discord.User:
                self.con.execute('DELETE FROM users WHERE id = ?', (o.id,))
                raise Exception('User does not have a NitroType account associated with their Discord account.')

            raise Exception(f'Nitro Type user **{nt_name}** does not exist.')

        return racer


def setup(bot):
    bot.add_cog(Game(bot))
