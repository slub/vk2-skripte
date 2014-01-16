'''
Created on Oct 14, 2013

@author: mendt
'''
# import database stuff 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.types import UserDefinedType
from sqlalchemy import func, desc, Column, Integer, Boolean, String

''' initialize database via sqlalchemy '''
Base = declarative_base()

def initialize_sql(engine):
    DBSession = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return DBSession()

class Geometry(UserDefinedType):
    def get_col_spec(self):
        return "GEOMETRY"
    
    def bind_expression(self, bindvalue):
        return func.ST_GeomFromText(bindvalue, type_=self)
    
    def column_expression(self, col):
        return func.ST_AsText(col, type_=self)
    
class Messtischblatt(Base):
    __tablename__ = 'messtischblatt'
    id = Column(Integer, primary_key=True)
    blattnr = Column(String(255))
    dateiname = Column(String(255))
    verzeichnispfad = Column(String(255))
    archivpfad = Column(String(255))
    isttransformiert = Column(Boolean)
    istkomprimiert = Column(Boolean)
    istaktiv = Column(Boolean)
    mdtype = Column(String(255))
    hasgeorefparams = Column(Integer)
    boundingbox = Column(Geometry)
    archivpfad_vk2 = Column(String(255))
    verzeichnispfad_original = Column(String(255))
    hasjpeg = Column(Boolean)
    jpegpath = Column(String(255))
    zoomify_properties = Column(String(255))
    zoomify_width = Column(Integer)
    zoomify_height = Column(Integer)
    
    @classmethod
    def all(cls, session):
        return session.query(Messtischblatt).order_by(desc(Messtischblatt.id))
    
    @classmethod
    def allForBlattnr(cls, blattnr, session):
        return session.query(Messtischblatt).filter(Messtischblatt.blattnr == blattnr).order_by(desc(Messtischblatt.id))
    
class MetadataTime(Base):
    __tablename__ = 'md_zeit'
    gid = Column(Integer, primary_key=True)
    typ = Column(String(255))
    art = Column(String(255))
    datierung = Column(Integer)
    id = Column(Integer)
    
    @classmethod
    def all(cls, session):
        return session.query(MetadataTime).order_by(desc(MetadataTime.id))
    
    @classmethod
    def getTimestampForMtb(cls, mtbid, session):
        return session.query(MetadataTime).filter(MetadataTime.typ == 'a5064').filter(MetadataTime.id == mtbid).first().datierung
    
class MesstischblattGrid(Base):
    __tablename__ = 'messtischblattgrid'
    blattnr = Column(String(255), primary_key=True)
    
    @classmethod
    def all(cls, session):
        return session.query(MesstischblattGrid).order_by(desc(MesstischblattGrid.blattnr))