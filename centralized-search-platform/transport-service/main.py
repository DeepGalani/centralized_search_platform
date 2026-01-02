import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime
from shared.messaging import RabbitMQPublisher

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost/marketplace")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Transport(Base):
    __tablename__ = "transports"
    id = Column(Integer, primary_key=True, index=True)
    carrier_id = Column(String, index=True)
    purchase_id = Column(Integer, index=True) # References Purchase
    pickup_location = Column(String)
    delivery_location = Column(String)
    schedule_date = Column(DateTime)
    status = Column(String) # SCHEDULED, IN_TRANSIT, DELIVERED

class TransportCreate(BaseModel):
    carrier_id: str
    purchase_id: int
    pickup_location: str
    delivery_location: str
    schedule_date: datetime.datetime
    status: str = "SCHEDULED"

class TransportResponse(TransportCreate):
    id: int
    class Config:
        orm_mode = True

app = FastAPI(title="Transport Service")
publisher = RabbitMQPublisher(queue_name="search_sync")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    try:
        publisher.connect()
    except Exception as e:
        print(f"MQ Error: {e}")

@app.post("/transports/", response_model=TransportResponse)
def create_transport(transport: TransportCreate, db: Session = Depends(get_db)):
    db_obj = Transport(**transport.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    event_data = transport.dict()
    event_data['id'] = db_obj.id
    event_data['entity_type'] = 'transport'
    event_data['schedule_date'] = db_obj.schedule_date.isoformat()

    try:
        publisher.publish_event("transport.created", event_data)
    except Exception as e:
        print(f"Failed to publish: {e}")

    return db_obj
