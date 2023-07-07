from __future__ import annotations

class Database():
    def __init__(self):
        self.name = None
        self.database = None
        self.member = None
        self.role = None
        self.sound = None


class NACDatabase(Database):
    def __init__(self):
        super().__init__()

        self.name = 'nac'


class VikingDatabase(Database):
    def __init__(self):
        super().__init__()

        self.name = 'viking'
