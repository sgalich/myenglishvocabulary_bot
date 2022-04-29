import os
from datetime import datetime
from logging import Handler
from typing import Type

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy import create_engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'bot'}
    id = Column(Integer, primary_key=True)    # Chat id
    username = Column(String(524))
    is_active = Column(Boolean, default=True)
    language_code = Column(String(64), default='en')
    last_message_datetime = Column(DateTime, nullable=False)
    is_editing = Column(Boolean, default=False)
    editing_card_id = Column(Integer)
    editing_status = Column(String(16))

    def __init__(self, **kwargs):
        self.last_message_datetime = datetime.now()
        for key, val in kwargs.items():
            setattr(self, key, val)


class Card(Base):
    __tablename__ = 'cards'
    __table_args__ = {'schema': 'bot'}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    definition = Column(String(8192))
    pronunciation = Column(String(512))
    synonyms = Column(String(2048))
    translation = Column(String(512))
    added = Column(Integer, default=1, nullable=False)
    shown = Column(Integer, default=0, nullable=False)
    learned = Column(Integer, default=0, nullable=False)
    flipped = Column(Integer, default=0, nullable=False)

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)
        self.title = self.title[:512]
        self.pronunciation = self.pronunciation[:512]
        self.definition = self.definition[:8192]
        self.synonyms = self.synonyms[:2048]


class LogMessage(Base):
    __tablename__ = 'logs'
    __table_args__ = {'schema': 'bot'}
    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime)
    user_id = Column(Integer)
    level = Column(String(8), default='INFO', nullable=False)
    text = Column(String(8192), nullable=False)

    def __init__(self, text: str, **kwargs):
        super().__init__()
        self.datetime = datetime.now()
        for key, val in kwargs.items():
            setattr(self, key, val)
        self.text = text[:8192]


class DataBase(Handler):
    CONNECT_TIMEOUT = 15
    DRIVER = 'mysql'
    DB_NAME = 'bot'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.kwargs = kwargs
        self.engine, self.connection, self.session = None, None, None
        self._initiate_session(**kwargs)

    def _initiate_session(self, **kwargs):
        """Connect to the Data Base."""
        connect_timeout = kwargs.get('connect_timeout', self.CONNECT_TIMEOUT)
        self.engine = create_engine(
            self._make_connection_string(**kwargs),
            connect_args={'connect_timeout': connect_timeout}
        )
        self.connection = self.engine.connect()    # Verify db connection
        self.engine.connect()
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()
        # 2. Make our first entry in db after the connection established.
        self.log('DB connection established')

    def _make_connection_string(self, **kwargs):
        """Create a connection string."""
        db_host = kwargs.get('DB_HOST', os.environ['DB_PARSERS_HOST'])
        db_port = kwargs.get('DB_PORT', os.environ['DB_PARSERS_PORT'])
        db_username = kwargs.get('DB_USERNAME', os.environ['DB_USERNAME'])
        db_password = kwargs.get('DB_PASSWORD', os.environ['DB_PASSWORD'])
        connection_string = (f'{self.DRIVER}://{db_username}:{db_password}@'
                             f'{db_host}:{db_port}/{self.DB_NAME}')
        return connection_string

    def _reconnect(self):
        self.session.rollback()
        self.engine.connect()

    def save(self, entity: Base) -> None:
        self.engine.connect()
        self.session.add(entity)
        self.session.commit()

    def select_one(self, table: Type[Base], **kwargs):
        self._reconnect()
        try:
            return self.session.query(table).filter_by(**kwargs).first()
        except NoResultFound:
            return None

    def select_all(self, table: Type[Base], **kwargs):
        self._reconnect()
        return self.session.query(table).filter_by(**kwargs).all()

    def delete(self, table: Type[Base], **kwargs) -> None:
        self._reconnect()
        self.session.query(table).filter_by(**kwargs).delete()
        self.session.commit()

    def update(self, entity: Base, **kwargs) -> None:
        self._reconnect()
        for key, val in kwargs.items():
            setattr(entity, key, val)
        self.session.merge(entity)
        self.session.commit()

    def emit(self, record):
        self._reconnect()
        self.log(self.format(record), level=record.levelname)

    def log(self, *args, **kwargs) -> None:
        self._reconnect()
        message = ' '.join(args)
        self.session.add(LogMessage(message, **kwargs))
        self.session.commit()
