from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)


class UserUpdate(Base):
    __tablename__ = 'user_update'
    children = relationship("UserAppend", back_populates="parent")


class UserAppend(Base):
    __tablename__ = 'user_append'
    parent_id = Column(Integer, ForeignKey('user_update.id'))
    parent = relationship("UserUpdate", back_populates="children")
