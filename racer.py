from datetime import datetime
from race import Race
from car import Car
from collections import namedtuple
from board import Board
from team import Team
from env import env
import aiohttp, re, json, discord

class Racer:

    def __init__(self, json):
        self.id = json['userID']
        self.username = json['username']
        self.country = json['country']
        self.gender = json['gender']
        self.title = json['title']
        self.experience = json['experience']
        self.level = json['level']
        self.looking_for_team = json['lookingForTeam'] == 1
        self.total_cars = json['totalCars']
        self.money = json['money']
        self.money_spent = json['moneySpent']
        self.nitros = json['nitros']
        self.nitros_used = json['nitrosUsed']
        self.medals_gold = json['placed1']
        self.medals_silver = json['placed2']
        self.medals_bronze = json['placed3']
        self.total_races = json['racesPlayed']
        self.longest_session = json['longestSession']
        self.avg_speed = json['avgSpeed']
        self.highest_speed = json['highestSpeed']
        self.achievment_points = json['achievementPoints']
        self.allow_friend_requests = json['allowFriendRequests'] == 1
        self.profile_views = json['profileViews']
        self.created_at = datetime.fromtimestamp(json['createdStamp'])
        self.tag = json['tag']
        self.races = [Race(log) for log in json['raceLogs']]
        self.cars = [Car(c[0], c[2], c[1] == 'owned') for c in json['cars']]

        self._team_id = json['teamID']
        self._car_id = json['carID']
        self._car_hue_angle = json['carHueAngle']
        self._display_name = json['displayName']
        self._membership = json['membership']

        self.car = Car(self._car_id, self._car_hue_angle)

        self.board_season = Board({"board": 'season', "typed": 0, "secs": 0, "played": 0, "errs": 0, "rank": 0})
        self.board_monthly = Board({"board": 'monthly', "typed": 0, "secs": 0, "played": 0, "errs": 0, "rank": 0})
        self.board_weekly = Board({"board": 'weekly', "typed": 0, "secs": 0, "played": 0, "errs": 0, "rank": 0})
        self.board_daily = Board({"board": 'daily', "typed": 0, "secs": 0, "played": 0, "errs": 0, "rank": 0})

        for b in json['racingStats']:
            if b['board'] == 'season':
                board = self.board_season
            elif b['board'] == 'monthly':
                board = self.board_monthly
            elif b['board'] == 'weekly':
                board = self.board_weekly
            elif b['board'] == 'daily':
                board = self.board_daily
            else:
                continue

            board.typed = b['typed']
            board.secs = b['secs']
            board.games_played = b['played']
            board.errors = b['errs']
            board.rank = b['rank']

    @property
    def money_earned(self):
        return self.money + self.money_spent

    @property
    def is_gold(self):
        return self._membership == 'gold'

    @property
    def profile_url(self):
        return f'https://www.nitrotype.com/racer/{self.username}'

    @property
    def display_name(self):
        return self._display_name or self.username

    @property
    def display_name_wtag(self):
        return (f'[{self.tag}] ' if self.tag else '') + (self._display_name or self.username)

    @property
    def flag_icon(self):
        if not self.country:
            return ''

        OFFSET = ord(u'\U0001F1E6') - ord('A')
        uc = f'{ord(self.country[0]) + OFFSET:x}-{ord(self.country[1]) + OFFSET:x}'
        return f'https://assets-cdn.github.com/images/icons/emoji/unicode/{uc}.png'

    def setup_embed(self, thumbnail=True):
        e = discord.Embed(colour=0xFFC720 if self.is_gold else 0xEEEEEE)
        e.set_author(name=self.display_name_wtag, url=self.profile_url, icon_url=self.flag_icon)
        e.title = self.title
        e.description = u'\u200B'

        if thumbnail:
            e.set_thumbnail(url=self.car.thumbnail)

        return e

    async def apply_roles(self, bot, user):
        racer_roles = []

        if self.tag:
            team = await Team.get(self.tag)

            if self.id == team.captain_id:
                racer_roles.append('Captain')
            elif discord.utils.get(team.members, id=self.id).role == 'officer':
                racer_roles.append('Officer')

        if self.board_weekly.games_played >= 500:
            racer_roles.append('Active')

        if self.board_weekly.accuracy >= 97:
            racer_roles.append('Accurate')

        if self.board_weekly.avg_speed >= 100:
            racer_roles.append('Fast')

        if self.created_at.year <= 2014:
            racer_roles.append('Veteran')

        if self.longest_session >= 800:
            racer_roles.append('Sessionist')

        if self.money >= 10_000_000:
            racer_roles.append('Wealthy')

        if self.is_gold:
            racer_roles.append('Gold')

        user_roles = [r.name for r in user.roles]
        roles = list(filter(lambda r: (r.name not in env['ROLE_NAMES'] and r.name in user_roles) or r.name in racer_roles, user.server.roles))
        await bot.replace_roles(user, *roles)
        await bot.change_nickname(user, self.display_name_wtag)

    async def update(self):
        async with aiohttp.client.post(f'https://www.nitrotype.com/api/players-search', data={'term': self.username}) as r:
            if r.status != 200:
                return None

            json = await r.json()

        # Finding the currct user
        for user in json['data']:
            if user['userID'] == self.id:
                json = user
                break

        if not json.get('userID'):
            await Racer.get(self.username, racer=self)
            return

        self.country = json['country']
        self.gender = json['gender']
        self.level = json['level']
        self.avg_speed = json['avgSpeed']
        self.title = json['title']
        self.total_races = json['racesPlayed']
        self.allow_friend_requests = json['allowFriendRequests']
        self.tag = json['tag']
        self.tagColor = json['tagColor']
        self.looking_for_team = json['lookingForTeam'] == 1

        self._display_name = json['displayName']
        self._team_id = json['teamID']
        self._membership = json['membership']
        self._car_id = json['carID']
        self._car_hue_angle = json['carHueAngle']

        self.car = Car(self._car_id, self._car_hue_angle)

    @staticmethod
    async def get(nt_name, update=False, racer=None):
        """
        Gets racer info for the given nt username.
        """

        async with aiohttp.client.get(f'https://www.nitrotype.com/racer/{nt_name}') as r:
            if r.status != 200:
                return None

            text = await r.text()
            match = re.search('RACER_INFO:\s+(\{.+?\}),\s+};', text, re.S)
            if not match:
                return None

            if racer:
                racer.__init__(json.loads(match.group(1)));r = racer
            else:
                r = Racer(json.loads(match.group(1)))

            if update:
                await r.update()

            return r
