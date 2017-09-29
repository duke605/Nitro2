from util import cancelable
from racer import Racer
import discord, asyncio


class Tasks:

    def __init__(self, bot):
        self.bot = bot
        self._tasks = []

    def __unload(self):
        for task in self._tasks:
            task.cancel()

    def add_task(self, coro):
        self._tasks.append(self.bot.loop.create_task(coro))

    async def on_ready(self):
        self.add_task(self.update_racers())

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
