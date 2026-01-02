#!/bin/bash

echo "Creating sample offers..."

# Create offers for seller_1
curl -X POST http://localhost:8001/offers/ \
  -H "Content-Type: application/json" \
  -d '{
    "seller_id": "seller_1",
    "vin": "VIN123456789",
    "make": "Toyota",
    "model": "Camry",
    "year": 2020,
    "price": 25000,
    "location": "New York",
    "condition": "Used - Excellent"
  }'

curl -X POST http://localhost:8001/offers/ \
  -H "Content-Type: application/json" \
  -d '{
    "seller_id": "seller_1",
    "vin": "VIN987654321",
    "make": "Honda",
    "model": "Civic",
    "year": 2021,
    "price": 22000,
    "location": "Los Angeles",
    "condition": "New"
  }'

curl -X POST http://localhost:8001/offers/ \
  -H "Content-Type: application/json" \
  -d '{
    "seller_id": "seller_2",
    "vin": "VIN555666777",
    "make": "BMW",
    "model": "3 Series",
    "year": 2022,
    "price": 45000,
    "location": "Chicago",
    "condition": "Certified Pre-Owned"
  }'

echo -e "\n✅ Sample data created! Wait 2-3 seconds for indexing..."
sleep 3
echo "Ready to search!"
