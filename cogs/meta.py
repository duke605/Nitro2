from discord.ext import commands
from collections import Counter
from datetime import datetime
import os, discord, psutil


class Meta:

    def __init__(self, bot):
        self.bot = bot
        self.version = '0.2.3'
        self.counter = Counter()

    async def on_command_completion(self, command, ctx):
        self.counter[command.name] += 1

    @commands.command(pass_context=True, aliases=['info'], description='Shows information about the bot.')
    async def about(self, ctx):
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

def setup(bot):
    bot.add_cog(Meta(bot))
