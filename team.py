from datetime import datetime
from board import Board
import aiohttp

class TeamMember:

    def __init__(self, tag, json):
        self.id = json['userID']
        self.tag = tag
        self.username = json['username']
        self.membership = json['membership']
        self.level = json['level']
        self.avg_speed = json['avgSpeed']
        self.title = json['title']
        self.country = json['country']
        self.gender = json['gender']
        self.car_id = json['carID']
        self.car_hue_angle = json['carHueAngle']
        self.last_login = json['lastLogin']
        self.status = json['status']
        self.join_stamp = datetime.fromtimestamp(json['joinStamp'])
        self.role = json['role']

        self._display_name = json['displayName']

    @property
    def display_name(self):
        return self._display_name or self.username

    @property
    def display_name_wtag(self):
        return (f'[{self.tag}] ' if self.tag else '') + (self._display_name or self.username)

class Team:

    def __init__(self, json):
        self.id = json['info']['teamID']
        self.captain_id = json['info']['userID']
        self.captain_username = json['info']['username']
        self.captain_display_name = json['info']['displayName']
        self.tag = json['info']['tag']
        self.tag_colour = int(f"0x{json['info']['tagColor']}", 16)
        self.name = json['info']['name']
        self.other_requirements = json['info']['otherRequirements']
        self.member_count = json['info']['members']
        self.enrollment = json['info']['enrollment']
        self.profile_views = json['info']['profileViews']
        self.last_activity = datetime.fromtimestamp(json['info']['lastActivity'])
        self.last_modified = datetime.fromtimestamp(json['info']['lastModified'])
        self.created_at = datetime.fromtimestamp(json['info']['createdStamp'])

        self.members = [TeamMember(self.tag, m) for m in json['members']]

        self._min_level = json['info']['minLevel']
        self._min_speed = json['info']['minSpeed']

        self.board_season = Board({"board": 'season', "typed": 0, "secs": 0, "played": 0, "errs": 0, "rank": 0})
        self.board_monthly = Board({"board": 'monthly', "typed": 0, "secs": 0, "played": 0, "errs": 0, "rank": 0})
        self.board_weekly = Board({"board": 'weekly', "typed": 0, "secs": 0, "played": 0, "errs": 0, "rank": 0})
        self.board_daily = Board({"board": 'daily', "typed": 0, "secs": 0, "played": 0, "errs": 0, "rank": 0})

        for b in json['stats']:
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
    def min_level(self):
        if self._min_level == 0:
            return 'Any Level'

        return self._min_level

    @property
    def min_speed(self):
        if self._min_speed == 0:
            return 'Any Speed'

        return f'{self._min_speed} WPM'

    @property
    def display_name(self):
        return f'[{self.tag}] {self.name}'

    @property
    def url(self):
        return f'https://www.nitrotype.com/team/{self.tag}'

    @staticmethod
    async def get(tag):
        async with aiohttp.client.get(f'https://www.nitrotype.com/api/teams/{tag}') as r:
            if r.status != 200:
                return None

            json = await r.json()

        if not json['success']:
            return None

        return Team(json['data'])
