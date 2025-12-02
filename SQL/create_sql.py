from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.mysql import DATETIME

Base = declarative_base()

# Define the table as a Python class
class Experiment(Base):
    __tablename__ = "experiments_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    req_id = Column(Integer, nullable=False)
    exp_id = Column(Integer, nullable=False)
    gen_at = Column(DATETIME(fsp=3), nullable=False)
    server_in = Column(DATETIME(fsp=3), nullable=True)
    server_out = Column(DATETIME(fsp=3), nullable=True)
    model_in = Column(DATETIME(fsp=3), nullable=False)
    model_out = Column(DATETIME(fsp=3), nullable=False)
    minio_in = Column(DATETIME(fsp=3), nullable=True)
    minio_out = Column(DATETIME(fsp=3), nullable=True)
    db_in = Column(DATETIME(fsp=3), nullable=True)
    db_out = Column(DATETIME(fsp=3), nullable=True)
    dpse_in = Column(DATETIME(fsp=3), nullable=True)
    dpse_out = Column(DATETIME(fsp=3), nullable=True)
    cpu_usage = Column(Float, nullable=True)
    gpu_usage = Column(Float, nullable=True)
    gpu_vram_usage = Column(Float, nullable=True)
    gpu_temperature = Column(Float, nullable=True)
    gpu_power = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    process_count = Column(Integer, nullable=True)
    fps = Column(Integer, nullable=True)
    device = Column(String(50), nullable=True)
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


DATABASE_URL = "mysql+mysqlconnector://root:root@localhost:3307/wf5"
# Create engine & session factory
engine = create_engine(DATABASE_URL, echo=True, pool_size=30,
    max_overflow=60)  # echo=True logs SQL
SessionLocal = sessionmaker(bind=engine)

# Create tables in the database
Base.metadata.create_all(engine)

