from EranoxAuth.Engine.Engine import Engine


class Sqlite(Engine):
    def __init__(self, engine_path='sqlite:///:memory:'):
        self.engine_path = engine_path
        Engine.__init__(self)
