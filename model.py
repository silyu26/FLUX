from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base  # import shared Base
from sqlalchemy.dialects.mysql import DATETIME

class Experiment(Base):
    __tablename__ = "experiments_data"

    req_id = Column(Integer, primary_key=True, autoincrement=True)
    exp_id = Column(Integer, nullable=False)
    gen_at = Column(DATETIME(fsp=3), nullable=False)
    server_in = Column(DATETIME(fsp=3), nullable=True)
    server_out = Column(DATETIME(fsp=3), nullable=True)
    model_in = Column(DATETIME(fsp=3), nullable=False)
    model_out = Column(DATETIME(fsp=3), nullable=False)
    db_in = Column(DATETIME(fsp=3), nullable=True)
    db_out = Column(DATETIME(fsp=3), nullable=True)
    dpse_in = Column(DATETIME(fsp=3), nullable=True)
    dpse_out = Column(DATETIME(fsp=3), nullable=True)

    weather = relationship("WeatherData", back_populates="experiment", uselist=False, cascade="all, delete-orphan")


class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    precipitation = Column(Float, nullable=False)
    temp_max = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    wind = Column(Float, nullable=False)

    experiment_id = Column(Integer, ForeignKey("experiments_data.req_id"), nullable=False, unique=True)

    experiment = relationship("Experiment", back_populates="weather")