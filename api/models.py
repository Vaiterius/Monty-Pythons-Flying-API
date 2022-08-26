from sqlite3 import Date
from sqlalchemy import Column, Integer, String, DateTime

from .database import Base


class Script(Base):
    """Maps all the scripts from Monty Python's Flying Circus.
    
    Original HTML hosted on: http://www.ibras.dk/montypython/justthewords.htm
    """
    __tablename__ = "scripts"

    index = Column(Integer, primary_key=True)
    episode = Column(Integer)
    episode_name = Column(String)
    segment = Column(String)
    type = Column(String)
    actor = Column(String)
    character = Column(String)
    detail = Column(String)
    record_date = Column(DateTime)
    series = Column(String)
    transmission_date = Column(DateTime)

    nested_sketches: dict|None = None  # Store upon first request.

