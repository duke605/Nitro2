from datetime import datetime
from bs4 import BeautifulSoup
import aiohttp, asyncio, re, json, discord


class News:

    def __init__(self, title, comments):
        self.title = title
        self.comments = []

        for c in comments:
            self.comments.append(News.Comment(self, c))

    @staticmethod
    async def get():
        async with aiohttp.client.get('https://www.nitrotype.com/news/rss') as r:
            if r.status != 200:
                return None

            html = BeautifulSoup(await r.text(), 'html.parser')

        item = html.find('item')
        if not item:
            return None

        async with aiohttp.client.get(item.guid.string) as r:
            if r.status != 200:
                return None

            text = await r.text()

        j = re.search(r'COMMENTS: (\[.+\]),.+?COMMENT_COUNT', text, re.S)
        if not json:
            return None

        return News(item.title.string, json.loads(j.group(1)))

    class Comment:

        def __init__(self, blog, _dict):
            self.blog = blog
            self.racer = News.Comment.Racer(self, _dict)
            self.id = _dict['blogCommentID']
            self.comment = _dict['comment']
            self.created_at = datetime.fromtimestamp(_dict['createdStamp'])
            self.moderator_comment = _dict['moderatorComment']
            self.admin_comment = _dict['adminComment']

        @property
        def colour(self):
            if self.moderator_comment:
                self.colour = 0x51ceff
            elif self.admin_comment:
                self.colour = 0xff5151

            return 0xcacbce

        def to_embed(self):
            print('s')
            embed = discord.Embed(description=f'\u200B\n{self.comment}', title=self.racer.title, colour=self.colour)
            embed.set_author(name=self.racer.display_name, url=self.racer.url, icon_url=self.racer.flag_icon)
            embed.add_field(name='Posted', value=self.created_at.strftime('%b %d, %Y at %I:%M %p').replace(' 0', ' '))
            embed.set_footer(text=self.id)

            return embed

        class Racer:

            def __init__(self, comment, _dict):
                self.comment = comment
                self._display_name = _dict['displayName']
                self.username = _dict['username']
                self.tag = _dict['tag']
                self.title = _dict['title']
                self.country = _dict['country']

            @property
            def display_name(self):
                if self.tag:
                    return f'[{self.tag}] {self._display_name or self.username}'

                return f'{self._display_name or self.username}'

            @property
            def url(self):
                return f'https://www.nitrotype.com/racer/{self.username}'

            @property
            def flag_icon(self):
                if not self.country:
                    return ''

                OFFSET = ord(u'\U0001F1E6') - ord('A')
                uc = f'{ord(self.country[0]) + OFFSET:x}-{ord(self.country[1]) + OFFSET:x}'
                return f'https://assets-cdn.github.com/images/icons/emoji/unicode/{uc}.png'
