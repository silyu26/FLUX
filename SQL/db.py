from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+mysqlconnector://root:root@localhost:3307/wf16"

engine = create_engine(DATABASE_URL, echo=True,pool_size=30,
    max_overflow=60)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()