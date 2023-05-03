from sqlalchemy import Column, Integer, TIMESTAMP, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Dates(Base):
    __tablename__ = 'dates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(TIMESTAMP, nullable=False)
    theme = Column(String(255), nullable=True)
    mariadb_engine = "InnoDB"


class Woman(Base):
    __tablename__ = 'Woman'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)


class SciFi(Base):
    __tablename__ = 'Scifi'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)


class Other(Base):
    __tablename__ = 'Other'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
