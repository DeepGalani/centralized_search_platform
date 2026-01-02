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

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String, index=True)
    offer_id = Column(Integer, index=True) # References Offer
    amount = Column(Float)
    status = Column(String)
    purchase_date = Column(DateTime, default=datetime.datetime.utcnow)

class PurchaseCreate(BaseModel):
    buyer_id: str
    offer_id: int
    amount: float
    status: str = "COMPLETED"

class PurchaseResponse(PurchaseCreate):
    id: int
    purchase_date: datetime.datetime
    class Config:
        orm_mode = True

app = FastAPI(title="Purchase Service")
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

@app.post("/purchases/", response_model=PurchaseResponse)
def create_purchase(purchase: PurchaseCreate, db: Session = Depends(get_db)):
    db_obj = Purchase(**purchase.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    event_data = purchase.dict()
    event_data['id'] = db_obj.id
    event_data['entity_type'] = 'purchase'
    event_data['purchase_date'] = db_obj.purchase_date.isoformat()

    try:
        publisher.publish_event("purchase.created", event_data)
    except Exception as e:
        print(f"Failed to publish: {e}")
        
    return db_obj
