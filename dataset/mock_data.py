import random
from typing import Dict, Any

# Mock database for all the necessary data
MOCK_DATABASE = {
    # Simulates a payment gateway with order and transaction details
    "payment_gateway": {
        "order_12345": {
            "customer_id": "cust_987",
            "amount": 25.50,
            "transactions": [
                {"id": "tx_abc", "amount": 25.50, "status": "confirmed"},
                {"id": "tx_def", "amount": 25.50, "status": "confirmed"}
            ]
        }
    },
    # Simulates a courier management system
    "couriers": {
        "courier_A": {
            "reputation_score": 0.85,
            "vehicle_capacity": "large",
            "status": "available",
            "location": (40.7128, -74.0060) # New York City
        },
        "courier_B": {
            "reputation_score": 0.30,
            "vehicle_capacity": "small",
            "status": "en_route_to_pickup",
            "location": (40.7306, -73.9995) # Near pickup location
        },
        "courier_C": {
            "reputation_score": 0.95,
            "vehicle_capacity": "medium",
            "status": "en_route_to_pickup",
            "location": (40.7580, -73.9855) # Times Square
        }
    },
    # Simulates a weather service
    "weather_service": {
        "New York": {
            "alert": "severe_rain_warning",
            "reroute_required": True
        },
        "Los Angeles": {
            "alert": "none",
            "reroute_required": False
        }
    }
}

# Simulates the order details with item sizes
ORDER_ITEMS_DATA = {
    "order_12345": {
        "items": [
            {"item_id": "item_1", "size": "small"},
            {"item_id": "item_2", "size": "small"},
            {"item_id": "item_3", "size": "bulky"}
        ]
    }
}