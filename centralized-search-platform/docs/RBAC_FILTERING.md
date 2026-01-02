# Role-Based Access Control (RBAC) - How It Works

## Overview
The search API implements security through **query-time filtering** in Elasticsearch. Each user role sees different data based on their permissions.

## How Role Filtering Works

### 1. Request Headers
Every search request includes:
```javascript
headers: {
  'user-type': 'Seller',  // The role
  'user-id': 'seller_1'   // The user's ID
}
```

### 2. Backend Filter Logic
The search service (`search-service/main.py`) applies different Elasticsearch filters based on the role:

#### **Seller** - Most Restrictive
```python
if user_type == "Seller":
    query_body["bool"]["filter"].append({"term": {"seller_id": user_id}})
    query_body["bool"]["filter"].append({"term": {"entity_type": "offer"}})
```
**Result**: Sellers only see their OWN offers (where `seller_id` matches their `user_id`)

#### **Buyer** - Moderate Access
```python
elif user_type == "Buyer":
    rbac_filter = {
        "bool": {
            "minimum_should_match": 1,
            "should": [
                {"term": {"entity_type": "offer"}},  # All offers
                {
                    "bool": {
                        "filter": [
                            {"term": {"entity_type": "purchase"}},
                            {"term": {"buyer_id": user_id}}  # Only their purchases
                        ]
                    }
                }
            ]
        }
    }
```
**Result**: Buyers see ALL offers + ONLY their own purchases

#### **Carrier** - Domain-Specific Access
```python
elif user_type == "Carrier":
    query_body["bool"]["filter"].append({"term": {"entity_type": "transport"}})
    query_body["bool"]["filter"].append({"term": {"carrier_id": user_id}})
```
**Result**: Carriers only see transports assigned to them

#### **Agent** - Full Access
```python
elif user_type == "Agent":
    pass  # No filters applied
```
**Result**: Agents see EVERYTHING across all entities

## Example Scenarios

### Scenario 1: Seller searches for "Honda"
- **User**: seller_1
- **Query**: "Honda"
- **Filter Applied**: `seller_id = seller_1` AND `entity_type = offer`
- **Results**: Only Honda offers created by seller_1

### Scenario 2: Buyer searches for "Honda"
- **User**: buyer_1
- **Query**: "Honda"
- **Filter Applied**: `entity_type = offer` OR (`entity_type = purchase` AND `buyer_id = buyer_1`)
- **Results**: ALL Honda offers from ALL sellers + any purchases by buyer_1

### Scenario 3: Agent searches for "Honda"
- **User**: agent_1
- **Query**: "Honda"
- **Filter Applied**: None
- **Results**: ALL Honda-related records (offers, purchases, transports)

## Security Implementation

The filtering happens at the **Elasticsearch query level**, meaning:
1. ✅ Data never leaves the database if the user doesn't have access
2. ✅ Fast (index-level filtering)
3. ✅ Scalable to millions of records
4. ✅ Cannot be bypassed from the frontend

## Code Location
See: `/home/deep/Project2/centralized-search-platform/search-service/main.py` (lines 166-220)
