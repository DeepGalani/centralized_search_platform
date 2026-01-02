import asyncio
import aiohttp
import random
import time
import sys

# Targets
OFFER_URL = "http://localhost:8001/offers/"
TOTAL_RECORDS = 1000
CONCURRENCY = 50  # Number of concurrent workers (simulating multiple users)
BATCH_SIZE = 100   # Requests per worker per batch

MAKES = ["Toyota", "Ford", "Honda", "BMW", "Mercedes", "Tesla", "Audi", "Chevrolet", "Nissan", "Hyundai"]
MODELS = ["Camry", "F-150", "Civic", "3 Series", "C-Class", "Model 3", "A4", "Silverado", "Altima", "Elantra"]
LOCATIONS = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"]
CONDITIONS = ["New", "Used - Excellent", "Used - Good", "Used - Fair", "Certified Pre-Owned"]

def generate_offer():
    return {
        "seller_id": f"seller_{random.randint(1, 50000)}",
        "vin": f"VIN{random.randint(100000000, 999999999)}",
        "make": random.choice(MAKES),
        "model": random.choice(MODELS),
        "year": random.randint(2010, 2025),
        "price": random.randint(5000, 150000),
        "location": random.choice(LOCATIONS),
        "condition": random.choice(CONDITIONS)
    }

async def post_offer(session):
    data = generate_offer()
    try:
        async with session.post(OFFER_URL, json=data) as resp:
            # We assume 200 OK mostly; ignoring body for speed
            return resp.status
    except Exception as e:
        return 0

async def worker(session, records_to_create):
    """A worker that keeps creating records until it hits its quota."""
    for _ in range(records_to_create):
        await post_offer(session)

async def main():
    print(f"🚀 Starting Data Load: Target {TOTAL_RECORDS} records")
    print(f"⚡ Concurrency: {CONCURRENCY} workers")
    
    start_time = time.time()
    records_created = 0
    
    async with aiohttp.ClientSession() as session:
        while records_created < TOTAL_RECORDS:
            # Launch a batch of workers
            # Each worker does BATCH_SIZE requests
            tasks = []
            current_batch = CONCURRENCY * BATCH_SIZE
            
            if records_created + current_batch > TOTAL_RECORDS:
                current_batch = TOTAL_RECORDS - records_created
            
            # Divide work among workers
            per_worker = current_batch // CONCURRENCY
            
            print(f"Processing batch... ({records_created}/{TOTAL_RECORDS})")
            
            workers = [worker(session, per_worker) for _ in range(CONCURRENCY)]
            await asyncio.gather(*workers)
            
            records_created += current_batch
            
            # Progress Report
            elapsed = time.time() - start_time
            rate = records_created / elapsed if elapsed > 0 else 0
            print(f"✅ Progress: {records_created} records. Rate: {rate:.0f} req/s")

    total_time = time.time() - start_time
    print(f"\n🎉 DONE! Created {records_created} records in {total_time:.2f} seconds.")

if __name__ == "__main__":
    # Check if user passed a custom count limit for testing
    if len(sys.argv) > 1:
        try:
            TOTAL_RECORDS = int(sys.argv[1])
        except:
            pass
            
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
