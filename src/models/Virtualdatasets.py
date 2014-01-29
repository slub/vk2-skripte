from src.models.Meta import Base
from src.models.Geometry import Geometry
from src.utils.Geometry import createBBoxFromPostGISString
from settings import srid_database

from sqlalchemy import Column, Integer, String, DateTime, desc


class Virtualdatasets(Base):
    __tablename__ = 'virtualdatasets'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    path = Column(String(255))
    timestamp = Column(DateTime(timezone=False))
    boundingbox = Column(Geometry)   
    lastupdate = Column(String(255))
    
    @classmethod
    def all(cls, session):
        return session.query(Virtualdatasets).order_by(desc(Virtualdatasets.id))

    
    @classmethod
    def by_id(cls, id, session):
        return session.query(Virtualdatasets).filter(Virtualdatasets.id == id).first()
    
    @classmethod 
    def by_timestamp(cls, timestamp, session):
        return session.query(Virtualdatasets).filter(Virtualdatasets.timestamp == timestamp).first()
    
    @property
    def BoundingBoxObj(self):
        return createBBoxFromPostGISString(self.boundingbox, srid_database)
 

  