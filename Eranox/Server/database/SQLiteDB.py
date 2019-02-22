from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Eranox.Server.database.Database import DB


class SQLiteDB(DB):
    def __init__(self, location: str = 'sqlite:///:memory:'):
        self.engine = create_engine(location, echo=True)
        self.create_database()
        self.Session = sessionmaker(bind=self.engine)
