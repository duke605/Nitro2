import re, json, aiohttp
from io import BytesIO

class Car:

    def __init__(self, id, hue, owned=True):
        self.id = id
        self.hue = hue
        self.owned = owned
        # '\['CARS', (\[\{.+?\}\])'

    @property
    def name(self):
        # Getting cars and their name
        with open('cars.json') as f:
            text = f.read()
            cars = json.loads(text)

        # Finding a car that matches the id
        for car in cars:
            if car['carID'] == self.id:
                return car['name']
        return 'Unknown'

    @property
    def thumbnail(self):
        if self.hue != 0:
            return f'https://www.nitrotype.com/cars/painted/{self.id}_small_1_{self.hue}.png'

        return f'https://www.nitrotype.com/cars/{self.id}_small_1.png'

    @property
    def image(self):
        if self.hue != 0:
            return f'https://www.nitrotype.com/cars/painted/{self.id}_large_1_{self.hue}.png'

        return f'https://www.nitrotype.com/cars/{self.id}_large_1.png'


    def __repr__(self):
        return f'<car.Car id={self.id}, hue={self.hue}, owned={self.owned}>'

    @staticmethod
    async def update_cars_json():
        async with aiohttp.client.get('https://www.nitrotype.com/index/543/bootstrap.js') as r:
            if r.status != 200:
                return False

            html = await r.text()

        match = re.search("\['CARS', (\[\{.+?\}\])", html, re.S)
        if not match:
            return False

        with open('cars.json', 'w') as f:
            f.write(match.group(1))

        return True
