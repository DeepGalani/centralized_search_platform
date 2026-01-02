import sys
import os

# quick hack to import shared module locally without packaging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime
from shared.messaging import RabbitMQPublisher

# Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost/marketplace")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

# DB Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Offer(Base):
    __tablename__ = "offers"
    
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(String, index=True)
    vin = Column(String, index=True)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    price = Column(Float)
    location = Column(String)
    condition = Column(String) # e.g., "New", "Used - Good"
    status = Column(String, default="ACTIVE") # ACTIVE, SOLD, CANCELLED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Pydantic Schemas
class OfferCreate(BaseModel):
    seller_id: str
    vin: str
    make: str
    model: str
    year: int
    price: float
    location: str
    condition: str

class OfferResponse(OfferCreate):
    id: int
    status: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True

# App
app = FastAPI(title="Offer Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RabbitMQ
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
        print(f"Warning: Could not connect to RabbitMQ on startup: {e}")

@app.post("/offers/", response_model=OfferResponse)
def create_offer(offer: OfferCreate, db: Session = Depends(get_db)):
    db_offer = Offer(**offer.dict())
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    
    # Publish Event
    event_data = offer.dict()
    event_data['id'] = db_offer.id
    event_data['entity_type'] = 'offer'
    event_data['status'] = 'ACTIVE'
    event_data['created_at'] = db_offer.created_at.isoformat()
    
    try:
        publisher.publish_event("offer.created", event_data)
    except Exception as e:
        print(f"Failed to publish event: {e}")
        # In a real app, we might want to transactions outbox pattern
    
    return db_offer

@app.get("/offers/{offer_id}", response_model=OfferResponse)
def read_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if offer is None:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer
