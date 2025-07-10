from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create SQLite engine and session
DATABASE_URL = "sqlite:///temperature.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()

# TemperatureForecast model
class TemperatureForecast(Base):
    __tablename__ = "temperature_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    region = Column(String, nullable=False)
    city = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    temperature = Column(Float, nullable=False)
    max_temperature = Column(Float, nullable=True)  # ✅ Added this line

# Create tables
Base.metadata.create_all(bind=engine)
