from discord.ext import commands
from collections import Counter
from datetime import datetime
from math import ceil
from util import Arguments
import os, discord, psutil, json


class Meta:

    def __init__(self, bot):
        self.bot = bot
        self.version = '0.3.5'
        self.counter = Counter()

    async def on_command_completion(self, command, ctx):
        self.counter[command.name] += 1

    @commands.command(pass_context=True, aliases=['info'], description='Shows information about the bot.')
    @commands.cooldown(1, 10, commands.cooldowns.BucketType.user)
    async def about(self, ctx):
        """
        {
            "usage": "about",
            "cooldown": 10
        }
        """
        e = discord.Embed(title='Official Development Server Invite', url='https://discord.gg/q3UNHq8', description='https://github.com/duke605/Nitro2')
        owner = await self.bot.get_user_info('136856172203474944')

        # Preparing field data
        uptime = datetime.utcnow() -self.bot.uptime
        hours, rem = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(rem, 60)
        days, hours = divmod(hours, 24)
        mem_usage = self.bot.process.memory_full_info().uss / 1024**2
        cpu_usage = self.bot.process.cpu_percent() / psutil.cpu_count()
        commands_used = sum(self.counter.values())
        commands_common = '\n'.join([f'**{name.capitalize()}: **{count}' for name, count in self.counter.most_common(3)])

        if days:
            time = f'{days}d {hours}h {minutes}m {seconds}s'
        else:
            time = f'{hours}h {minutes}m {seconds}s'

        # Fields
        e.add_field(name='Version', value=self.version, inline=False)
        e.add_field(name='Uptime', value=time)
        e.add_field(name='Process', value=f'{mem_usage:.2f} MiB\n{cpu_usage:.2f}% CPU')
        e.add_field(name='PID', value=f'{self.bot.process.pid}')
        e.add_field(name='Commands', value=f'**Used: **{commands_used}\n{commands_common}')
        e.set_author(name=str(owner), icon_url=owner.avatar_url)
        e.set_footer(text='Made with discord.py (%s)' % discord.__version__, icon_url='http://i.imgur.com/5BFecvA.png')

        await self.bot.say(embed=e)

    @commands.command(pass_context=True, name="help", description='Shows help information.')
    @commands.cooldown(1, 10, commands.cooldowns.BucketType.user)
    async def _help(self, ctx, *, msg=''):
        """
        {
            "usage": "help [command] [--page|-p num]",
            "cooldown": 10,
            "arguments": [
                {
                    "name": "command",
                    "type": "string",
                    "value": "The command you need help with. Leave blank this would if you want to see a list of commands."
                }
            ],
            "options": [
                {
                    "name": "--page|p",
                    "type": "int",
                    "value": "The help page you wish to retrieve. Starts at 1."
                }
            ]
        }
        """
        parser = Arguments(allow_abbrev=False, prog='help')
        parser.add_argument('command', nargs='?')
        parser.add_argument('-p', '--page', type=int, default=1)

        await self.bot.send_typing(ctx.message.channel)
        args = await parser.do_parse(self.bot, msg)

        if not args:
            return

        e = discord.Embed()
        if not args.command:
            if await Meta.write_help_to_embed(self.bot, args.page, e):
                await self.bot.say(None, embed=e)
            return

        cmd = self.bot.commands.get(args.command)
        if not cmd or cmd.hidden:
            await self.bot.say('Command not found.')

        j = json.loads(cmd.help)
        e.title = cmd.name.capitalize()
        e.description = cmd.description + u'\n\u200B'
        e.add_field(name='Usage', value=f'!{j["usage"]}')

        if cmd.aliases:
            e.add_field(name='Aliases', value=', '.join(cmd.aliases))

        e.add_field(name='Cooldown', value=f'{j.get("cooldown", 0)} Seconds')

        for a in j.get('arguments', []):
            e.add_field(name=f'{a["name"]}: {a["type"]}', value=a['value'], inline=False)

        for a in j.get('options', []):
            e.add_field(name=f'{a["name"]}: {a["type"]}', value=a['value'], inline=False)

        await self.bot.say(None, embed=e)

    @staticmethod
    async def write_help_to_embed(bot, page, e):
        e.clear_fields()

        SHOWN = 5
        page = max(1, page) - 1
        count = sum([1 for k in bot.commands if not bot.commands[k].hidden and k not in bot.commands[k].aliases])
        commands = [k for k in bot.commands if not bot.commands[k].hidden and k not in bot.commands[k].aliases]
        commands = commands[page * SHOWN:(page + 1) * SHOWN]

        if not commands:
            return False

        e.title = f'Help (Page {page + 1}/{int(ceil(count/SHOWN))})'
        e.description = u'Type `!help [command]` for more information about a specific command.\n\u200B'

        for command in commands:
            cmd = bot.commands[command]
            j = json.loads(cmd.help)
            aliases = '**Aliases: **' + ', '.join(cmd.aliases) + '\n' if cmd.aliases else ''
            value = f'**Usage: **!{j["usage"]}\n**Cooldown: **{j.get("cooldown", 0)} seconds\n{aliases}{cmd.description}'

            e.add_field(name=f'__**{cmd.name.capitalize()}**__', value=value, inline=False)

        return True

def setup(bot):
    bot.add_cog(Meta(bot))
