def create_database(engine, base):
    base.metadata.create_all(engine)
