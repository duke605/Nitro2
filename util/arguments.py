import argparse, shlex

class Arguments(argparse.ArgumentParser):

    def error(self, message):
        raise RuntimeError(message)

    async def do_parse(self, bot, msg):
        try:
            return self.parse_args(shlex.split(msg))
        except SystemExit:
            await bot.say(f'```{self.format_help()}```')
        except Exception as e:
            await bot.say(f'```{str(e)}```')

        return None
