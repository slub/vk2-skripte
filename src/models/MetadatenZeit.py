from src.models.Meta import Base

from sqlalchemy import Column, Integer, String, DateTime

class MetadatenZeit(Base):
    __tablename__ = 'md_zeit'
    __table_args__ = {'extend_existing':True}
    gid = Column(Integer, primary_key=True)
    id = Column(Integer)
    typ = Column(String(255))
    art = Column(String(255))
    datierung = Column(Integer)
    datierung_start = Column(Integer)
    datierung_ende = Column(Integer)
    time = Column(DateTime(timezone=False))
    
    @classmethod
    def getRefTimeForMesstischblatt(cls, id, session):
        return session.query(MetadatenZeit).filter(MetadatenZeit.id == id).filter(MetadatenZeit.typ == 'a5064').first()