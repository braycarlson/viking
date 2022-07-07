from gino import Gino
from model.guild import (
    NACDatabase,
    VikingDatabase
)

command = Gino()
lol = Gino()
nac = Gino()
viking = Gino()

vd = VikingDatabase()
nd = NACDatabase()


factory = {
    '186994904365400064': vd,
    '863292513141522433': nd
}


class Guild:
    def get(self, gid):
        guild = factory.get(gid)

        if guild is None:
            return None

        return guild

    def generate(self, attribute):
        return [
            getattr(factory[key], attribute)
            for key in factory.keys()
        ]
