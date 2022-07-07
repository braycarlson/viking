from dataclasses import dataclass


@dataclass
class Mode:
    def __init__(self, data, key):
        self._mode = data.get('stats').get(key)

    @property
    def kills(self):
        if self._mode is None:
            return '0'

        return self._mode.get('kills').get('displayValue')

    @property
    def matches(self):
        if self._mode is None:
            return '0'

        return self._mode.get('matches').get('displayValue')

    @property
    def wlr(self):
        if self._mode is None:
            return '0.00'

        return self._mode.get('winRatio').get('displayValue')

    @property
    def kdr(self):
        if self._mode is None:
            return '0.00'

        return self._mode.get('kd').get('displayValue')

    @property
    def wins(self):
        if self._mode is None:
            return '0'

        return self._mode.get('top1').get('displayValue')


# The TRN API includes a 'Lifetime' statistic, but due to formatting
# inconsistencies; I have opted to calculate it from the core modes.

@dataclass
class Lifetime:
    def __init__(self, solo, duo, squad):
        self._solo = solo
        self._duo = duo
        self._squad = squad

    @staticmethod
    def get_sum(*args):
        """
        A function to convert a tuple of strings to integers,
        and then add the sum of the integers.
        """

        integers = [int(arg.replace(',', '')) for arg in args]
        return sum(integers)

    @property
    def kills(self):
        total = self.get_sum(
            self._solo.kills,
            self._duo.kills,
            self._squad.kills
        )

        return f"{total:,}"

    @property
    def matches(self):
        total = self.get_sum(
            self._solo.matches,
            self._duo.matches,
            self._squad.matches
        )

        return f"{total:,}"

    @property
    def wlr(self):
        wins = self.get_sum(
            self._solo.wins,
            self._duo.wins,
            self._squad.wins
        )

        matches = self.get_sum(
            self._solo.matches,
            self._duo.matches,
            self._squad.matches
        )

        total = (wins / matches) * 100
        return f"{total:.2f}"

    @property
    def kdr(self):
        kills = self.get_sum(
            self._solo.kills,
            self._duo.kills,
            self._squad.kills
        )

        wins = self.get_sum(
            self._solo.wins,
            self._duo.wins,
            self._squad.wins
        )

        matches = self.get_sum(
            self._solo.matches,
            self._duo.matches,
            self._squad.matches
        )

        total = kills / (matches - wins)
        return f"{total:.2f}"

    @property
    def wins(self):
        total = self.get_sum(
            self._solo.wins,
            self._duo.wins,
            self._squad.wins
        )

        return f"{total:,}"
