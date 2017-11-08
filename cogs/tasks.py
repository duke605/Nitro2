from util import cancelable
from racer import Racer
from news import News
from io import StringIO
import discord, asyncio, traceback


class Tasks:

    def __init__(self, bot):
        self.bot = bot
        self._tasks = []

        self.bot.loop.create_task(self.add_task(self.update_racers()))
        self.bot.loop.create_task(self.add_task(self.get_comments()))

    def __unload(self):
        for task in self._tasks:
            task.cancel()

    async def add_task(self, coro):
        await self.bot.wait_until_ready()

        self._tasks.append(self.bot.loop.create_task(coro))

    @cancelable
    async def get_comments(self):
        while not self.bot.is_closed:
            try:
                settings = self.bot.db_connection.execute('SELECT * FROM settings LIMIT 1').fetchone()
                news = await News.get()
                comments = list(filter(lambda c: c.id > settings['last_comment'], news.comments))

                for c in comments:
                    embed = c.to_embed()
                    self.bot.db_connection.execute('UPDATE settings SET last_comment = ?', (c.id,))

                    for s in self.bot.servers:
                        news_channel = discord.utils.find(lambda channel: channel.name == 'nt-news', s.channels)
                        if not news_channel:
                            continue

                        await self.bot.send_message(news_channel, embed=embed)

                    await asyncio.sleep(1)

                comments = None
                news = None
                settings = None
                embed = None
                news_channel = None
            except Exception as ex:
                with StringIO() as out:
                    traceback.print_exception(type(ex), ex, ex.__traceback__, file=out)
                    out.seek(0)
                    error = out.read()

                print(error)

            await asyncio.sleep(60)

    @cancelable
    async def update_racers(self):
        while not self.bot.is_closed:
            c = self.bot.db_connection.cursor()

            for row in c.execute('SELECT * FROM users'):
                racer = await Racer.get(row['nitro_name'])
                if not racer:
                    continue

                for server in self.bot.servers:
                    member = server.get_member(row['id'])
                    if not member:
                        continue

                    try:
                        await racer.apply_roles(self.bot, member)
                    except Exception as e:
                        pass

            c.close()
            del c
            await asyncio.sleep(30 * 60)


def setup(bot):
    bot.add_cog(Tasks(bot))
