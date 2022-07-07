from abc import ABC


class Database(ABC):
    def __init__(self):
        self._name = None
        self._database = None
        self._member = None
        self._role = None
        self._sound = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, engine):
        self._engine = engine

    @property
    def member(self):
        return self._member

    @member.setter
    def member(self, member):
        self._member = member

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        self._role = role

    @property
    def sound(self):
        return self._sound

    @sound.setter
    def sound(self, sound):
        self._sound = sound


class VikingDatabase(Database):
    def __init__(self):
        self._name = 'viking'


class NACDatabase(Database):
    def __init__(self):
        self._name = 'nac'
