'''
Created on Jan 9, 2014

@author: mendt
'''
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

def initializeDb(sqlalchemy_engine):
    engine = create_engine(sqlalchemy_engine, encoding='utf8', echo=True)
    DBSession = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return DBSession()