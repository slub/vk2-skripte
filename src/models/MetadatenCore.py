from src.models.Meta import Base

from sqlalchemy import Column, Integer, String, Unicode

class MetadatenCore(Base):
    __tablename__ = 'md_core'
    __table_args__ = {'extend_existing':True}
    id = Column(Integer, primary_key=True)
    titel = Column(Unicode(255))
    serientitel = Column(String(255))
    gattung = Column(String(255))
    sachbegriffe = Column(String(255))
    beschreibung = Column(Unicode(255))
    technik = Column(String(255))
    masse = Column(String(255))
    massstab = Column(String(255))
    schlagworte = Column(String(255))
    ppn = Column(String(255))
    titel_short = Column(Unicode(70))
    
    @classmethod
    def by_id(cls, id, session):
        return session.query(MetadatenCore).filter(MetadatenCore.id == id).first()