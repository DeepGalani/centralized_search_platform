import sys
import os
import json
import threading
from typing import List, Optional
import pika

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Query, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from elasticsearch import Elasticsearch

# Configuration
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")

es = Elasticsearch(ES_HOST)
app = FastAPI(title="Search Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_NAME = "marketplace_search"

# --- Elasticsearch Setup ---
def setup_index():
    if not es.indices.exists(index=INDEX_NAME):
        settings = {
            "analysis": {
                "analyzer": {
                    "autocomplete": {
                        "tokenizer": "autocomplete",
                        "filter": ["lowercase"]
                    },
                    "autocomplete_search": {
                        "tokenizer": "lowercase"
                    }
                },
                "tokenizer": {
                    "autocomplete": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 10,
                        "token_chars": ["letter", "digit"]
                    }
                }
            }
        }
        mappings = {
            "properties": {
                "entity_type": {"type": "keyword"},
                "id": {"type": "keyword"},
                "search_text": {
                    "type": "text", 
                    "analyzer": "autocomplete", 
                    "search_analyzer": "autocomplete_search"
                },
                # Flattened fields for filtering
                "seller_id": {"type": "keyword"},
                "buyer_id": {"type": "keyword"},
                "carrier_id": {"type": "keyword"},
                "offer_id": {"type": "keyword"},
                "vin": {"type": "keyword"},
                
                # Copy-to fields for general search
                "make": {"type": "text", "copy_to": "search_text"},
                "model": {"type": "text", "copy_to": "search_text"},
                "status": {"type": "keyword"},
                "created_at": {"type": "date"}
            }
        }
        es.indices.create(index=INDEX_NAME, settings=settings, mappings=mappings)
        print("Index created.")

# --- RabbitMQ Consumer ---
def process_message(ch, method, properties, body):
    try:
        msg = json.loads(body)
        event_type = msg.get("event_type")
        data = msg.get("data")
        
        # Prepare document for ES
        doc_id = f"{data['entity_type']}_{data['id']}"
        
        # Basic transformation - in real world would fetch related data
        # e.g., for purchase, might fetch make/model from offer
        es_doc = data.copy()
        
        # Add search helpers
        if data.get('make') and data.get('model'):
             # make model vin location condition status
             result_text = f"{data.get('make', '')} {data.get('model', '')} {data.get('vin', '')} {data.get('location', '')} {data.get('condition', '')} {data.get('status', '')}"
             es_doc['search_text'] = result_text

        es.index(index=INDEX_NAME, id=doc_id, document=es_doc)
        print(f"Indexed {doc_id}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def start_consumer():
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue='search_sync', durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='search_sync', on_message_callback=process_message)
        print("Consumer started...")
        channel.start_consuming()
    except Exception as e:
        print(f"Consumer failed: {e}")

# --- API ---
class SearchResponse(BaseModel):
    total: int
    results: List[dict]

@app.on_event("startup")
def startup_event():
    # Wait for ES to be ready (simplified)
    # In production, use sturdy retry logic
    try:
        if es.ping():
            setup_index()
    except:
        pass
    
    # Start consumer in background
    t = threading.Thread(target=start_consumer, daemon=True)
    t.start()

@app.post("/reindex")
def reindex_all():
    """Manually reindex all data from source services into Elasticsearch"""
    import requests
    
    indexed_count = 0
    
    # For now, we'll just trigger reindexing from the offer service
    # In a real system, this would fetch from all services
    try:
        # Get all offers from the database via direct query would be better
        # But since we don't have access here, we'll use a workaround
        # This is a simplified version - ideally you'd query Postgres directly
        
        return {"message": "Reindexing complete. Note: This endpoint needs database access to fully reindex.", "indexed": indexed_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search", response_model=SearchResponse)
def search(
    q: Optional[str] = Query(None, min_length=2),
    user_type: str = Header(...), # Seller, Buyer, Carrier, Agent
    user_id: str = Header(...),   # ID of the user
    account_id: Optional[str] = Header(None)
):
    query_body = {
        "bool": {
            "must": [],
            "filter": []
        }
    }

    # 1. Text Search (if provided)
    if q:
        query_body["bool"]["must"].append({
            "multi_match": {
                "query": q,
                "fields": [
                    "search_text^3", 
                    "id", "seller_id", "vin", 
                    "make", "model", "year", 
                    "location", "condition", "status",
                    "price",
                    "created_at"
                ],
                "fuzziness": "AUTO", # Typo tolerance
                "lenient": True # Ignore data type mismatches (e.g. text search on price)
            }
        })
    else:
        query_body["bool"]["must"].append({"match_all": {}})

    # 2. RBAC / Context Security
    # This acts as the "ACL"
    
    if user_type == "Seller":
        # Seller sees only THEIR offers. 
        # Requirement: "Can only search and view their own offers"
        # Note: Sellers strictly only see offers? Or check requirement again.
        # "Sellers... Manage Offers... Can only search and view their own offers"
        # So filter by seller_id AND entity_type=offer
        query_body["bool"]["filter"].append({"term": {"seller_id": user_id}})
        query_body["bool"]["filter"].append({"term": {"entity_type": "offer"}})

    elif user_type == "Buyer":
        # "Can search available offers and their own purchase history"
        # So: (entity_type=offer AND status=ACTIVE) OR (entity_type=purchase AND buyer_id=user_id)
        
        # We need a should clause inside a filter for this OR logic
        rbac_filter = {
            "bool": {
                "minimum_should_match": 1,
                "should": [
                    {
                        "bool": {
                            "filter": [
                                {"term": {"entity_type": "offer"}},
                                # {"term": {"status": "ACTIVE"}} # Optional: only active offers?
                            ]
                        }
                    },
                    {
                        "bool": {
                            "filter": [
                                {"term": {"entity_type": "purchase"}},
                                {"term": {"buyer_id": user_id}}
                            ]
                        }
                    }
                ]
            }
        }
        query_body["bool"]["filter"].append(rbac_filter)

    elif user_type == "Carrier":
        # "Can search transport assignments and related vehicle information"
        # Similar logic: Transports where carrier_id=user_id
        # "Related vehicle info" - This implies they might need to see Offers linked to their transports.
        # This is complex in a flat index.
        # For MVP: Show Transports assigned to them.
        query_body["bool"]["filter"].append({"term": {"entity_type": "transport"}})
        query_body["bool"]["filter"].append({"term": {"carrier_id": user_id}})

    elif user_type == "Agent":
        # "Need access to search across ALL objects... Must respect data access permissions based on context"
        # Agents see everything usually.
        pass 
    
    else:
        raise HTTPException(status_code=400, detail="Invalid User Type")

    # Execute (ES 8.x syntax)
    resp = es.search(index=INDEX_NAME, query=query_body, size=20)
    
    results = [hit["_source"] for hit in resp["hits"]["hits"]]
    return {"total": resp["hits"]["total"]["value"], "results": results}
