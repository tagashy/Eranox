from sqlalchemy.ext.declarative import declarative_base
from Eranox.Server.database.SQLiteDB import SQLiteDB
Base = declarative_base
DEFAULT_ENGINE=SQLiteDB