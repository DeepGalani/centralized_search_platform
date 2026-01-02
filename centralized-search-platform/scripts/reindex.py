#!/usr/bin/env python3
"""
Reindex Script - Syncs all data from PostgreSQL to Elasticsearch

This script reads all records from the offers, purchases, and transports tables
and indexes them into Elasticsearch manually.
"""

import sys
import subprocess
import json
import time

# Configuration
DB_URL = "postgresql://admin:password@localhost:5432/marketplace"
ES_HOST = "http://localhost:9200"
INDEX_NAME = "marketplace_search"

def connect_db():
    return psycopg2.connect(DB_URL)

def connect_es():
    return Elasticsearch(ES_HOST)

def reindex_offers(conn, es):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, seller_id, vin, make, model, year, price, 
               location, condition, status, created_at
        FROM offers
    """)
    
    count = 0
    for row in cursor.fetchall():
        doc = {
            "id": row[0],
            "seller_id": row[1],
            "vin": row[2],
            "make": row[3],
            "model": row[4],
            "year": row[5],
            "price": row[6],
            "location": row[7],
            "condition": row[8],
            "status": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
            "entity_type": "offer",
            "search_text": f"{row[3]} {row[4]} {row[2]}"  # make model vin
        }
        
        doc_id = f"offer_{row[0]}"
        es.index(index=INDEX_NAME, id=doc_id, document=doc)
        count += 1
        
        if count % 100 == 0:
            print(f"Indexed {count} offers...")
    
    cursor.close()
    print(f"✅ Total offers indexed: {count}")
    return count

def reindex_purchases(conn, es):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, buyer_id, offer_id, amount, status, purchase_date
        FROM purchases
    """)
    
    count = 0
    for row in cursor.fetchall():
        doc = {
            "id": row[0],
            "buyer_id": row[1],
            "offer_id": row[2],
            "amount": row[3],
            "status": row[4],
            "purchase_date": row[5].isoformat() if row[5] else None,
            "entity_type": "purchase"
        }
        
        doc_id = f"purchase_{row[0]}"
        es.index(index=INDEX_NAME, id=doc_id, document=doc)
        count += 1
    
    cursor.close()
    print(f"✅ Total purchases indexed: {count}")
    return count

def reindex_transports(conn, es):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, carrier_id, purchase_id, pickup_location, 
               delivery_location, schedule_date, status
        FROM transports
    """)
    
    count = 0
    for row in cursor.fetchall():
        doc = {
            "id": row[0],
            "carrier_id": row[1],
            "purchase_id": row[2],
            "pickup_location": row[3],
            "delivery_location": row[4],
            "schedule_date": row[5].isoformat() if row[5] else None,
            "status": row[6],
            "entity_type": "transport"
        }
        
        doc_id = f"transport_{row[0]}"
        es.index(index=INDEX_NAME, id=doc_id, document=doc)
        count += 1
    
    cursor.close()
    print(f"✅ Total transports indexed: {count}")
    return count

def main():
    print("🔄 Starting reindexing process...")
    
    try:
        # Connect to services
        print("Connecting to PostgreSQL...")
        conn = connect_db()
        
        print("Connecting to Elasticsearch...")
        es = connect_es()
        
        # Reindex all entities
        start_time = time.time()
        
        total = 0
        total += reindex_offers(conn, es)
        total += reindex_purchases(conn, es)
        total += reindex_transports(conn, es)
        
        elapsed = time.time() - start_time
        
        print(f"\n🎉 Reindexing complete!")
        print(f"Total records indexed: {total}")
        print(f"Time taken: {elapsed:.2f} seconds")
        print(f"Rate: {total/elapsed:.0f} docs/sec")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
