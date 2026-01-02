# Centralized Search Platform - Usage Guide

## Quick Start

1.  **Start Infrastructure & Services**:
    ```bash
    cd centralized-search-platform
    docker-compose up --build -d
    ```
    Wait for all services to be healthy (approx 30-60s).

2.  **Start Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
    Access UI at `http://localhost:5173`.

3.  **Generate Data (10M Records Simulation)**:
    Note: The script spawns concurrent workers. Adjust `count` in script for massive loads.
    ```bash
    # Run the load script (requires python env)
    pip install aiohttp
    python scripts/load_data.py
    ```

## Architecture Usage

### API Endpoints
- **Offer Service**: `POST http://localhost:8001/offers/`
- **Search Service**: `GET http://localhost:8004/search`

### RBAC testing
In the UI, switch the user role in the top dropdown:
- **Seller**: Sees only their offers (Filtered by `seller_id`).
- **Buyer**: Sees All Offers + Their Purchases.
- **Carrier**: Sees Transports assigned to them.
- **Agent**: Sees Everything.

### Search Features
- **Typo Tolerance**: Try searching "Toyota" as "Toyoda".
- **Autocomplete**: Partial matches on VINs or models work automatically via `edge_ngram` indexers.

## Data Loading Strategy for 10M Records
To achieve 10M records:
1.  Navigate to `scripts/load_data.py`.
2.  Increase the loop count or number of workers.
3.  The script uses `aiohttp` for async non-blocking I/O, capable of generating thousands of requests per second depending on your machine's CPU/Network.

## Deployment
All services are containerized. Use `docker-compose up` to deploy the entire stack locally.
