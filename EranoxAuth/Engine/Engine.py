from sqlalchemy import create_engine


class Engine(object):
    engine_path = NotImplemented

    def __init__(self):
        self.engine = create_engine(self.engine_path, echo=True)
