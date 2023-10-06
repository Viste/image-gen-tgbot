from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, nullable=False)
    tg_username = Column(String(255), nullable=True)
    sub_start = Column(DateTime, nullable=True)
    sub_end = Column(DateTime, nullable=True)
    sub_state = Column(String(50), nullable=False, default='inactive')
    mariadb_engine = "InnoDB"

class Workers(Base):
    __tablename__ = 'workers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    theme = Column(String(255), nullable=True)
    prompt = Column(Text, nullable=False)
    posted = Column(Boolean, nullable=False, default=False)
    mariadb_engine = "InnoDB"
