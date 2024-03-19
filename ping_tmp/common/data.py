from sqlalchemy import create_engine
import os


class BaseEngine(object):
    def __init__(self, base_dir='./booya_log/cache', dbname='data'):
        db_path = os.path.join(base_dir, dbname)
        url = f'sqlite:///{db_path}'
        self.engine = create_engine(url, echo=True)

from sqlalchemy.orm import sessionmaker

class BaseSession(BaseEngine):
    def __init__(self):
        super().__init__()
        Session = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
        )
        self.session = Session()
