class Board:

    def __init__(self, json):
        self.board = json['board']
        self.typed = json['typed']
        self.secs = json['secs']
        self.games_played = json['played']
        self.errors = json['errs']
        self.rank = json['rank']

    @property
    def avg_speed(self):
        if self.secs == 0:
            return 0

        return int(round(self.typed / 5 / (float(self.secs) / 60)))

    @property
    def accuracy(self):
        if self.typed == 0:
            return 0

        return round(100 - self.errors / self.typed * 100, 2)

    def add_field(self, e):
        value = f'**Races: **{self.games_played:,}\n**Avg Speed: **{self.avg_speed} WPM\n**Accuracy: **{self.accuracy}%\n**Rank: **{self.rank:,}'

        if self.board == 'season':
            name = 'Season'
        elif self.board == 'monthly':
            name = '30 Days'
        elif self.board == 'weekly':
            name = '7 Days'
        else:
            name = '24 Hours'

        e.add_field(name=name, value=value)
