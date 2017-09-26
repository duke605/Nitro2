from datetime import datetime


class Race:

    def __init__(self, json):
        self.wpm = json['value']
        self.date = datetime.fromtimestamp(json['stamp'])
        self.position = json['place']
        self.letters_typed = json['typed']
        self.time_completed = json['secs']
        self.errors = json['errs']

    @property
    def medal_colour(self):
        colours = {1: "#fee78b", 2: "#cecece", 3: "#9b671c"}
        return colours.get(self.position, '#2d8acd')
