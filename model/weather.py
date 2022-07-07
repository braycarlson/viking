from dataclasses import dataclass
from utilities.format import format_utc

@dataclass
class Forecast:
    __slots__ = (
        'city',
        'country',
        'conditions',
        'condition',
        'description',
        'temperature',
        'low_temperature',
        'high_temperature',
        'wind',
        'humidity',
        'pressure',
        'observed'
    )

    def __init__(self, data):
        self.city = data.get('name')
        self.country = data.get('sys').get('country')
        self.conditions = data.get('weather')
        self.temperature = data.get('main').get('temp')
        self.low_temperature = data.get('main').get('temp_min')
        self.high_temperature = data.get('main').get('temp_max')
        self.wind = data.get('wind').get('speed')
        self.humidity = data.get('main').get('humidity')
        self.pressure = data.get('main').get('pressure')
        self.observed = data.get('dt')

        for condition in self.conditions:
            self.condition = condition.get('main').title()
            self.description = condition.get('description').title()

    @property
    def fahrenheit(self):
        return (self.temperature * 9/5) + 32

    @property
    def low_fahrenheit(self):
        return (self.low_temperature * 9/5) + 32

    @property
    def high_fahrenheit(self):
        return (self.high_temperature * 9/5) + 32

    @property
    def kmh_wind(self):
        return self.wind * 3600 / 1000

    @property
    def mph_wind(self):
        return self.wind / 0.44704

    @property
    def date(self):
        return format_utc(self.observed)
