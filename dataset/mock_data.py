import random
from typing import Dict, Any

MOCK_DATABASE: Dict[str, Any] = {
    "payment_gateway": {
        "order_12345": {
            "customer_id": "cust_987",
            "amount": 249.0,
            "transactions": [
                {"id": "tx_abc", "amount": 249.0, "status": "confirmed"},
                {"id": "tx_def", "amount": 249.0, "status": "authorized"}
            ]
        }
    },
    "couriers": {
        "courier_A": {
            "reputation_score": 0.85,
            "vehicle_capacity": {"type": "van", "vol_cap_l": 500, "weight_cap_kg": 200},
            "special_equipment": {"insulated_container": False},
            "status": "available",
            "location": (40.7128, -74.0060) # New York City
        },
        "courier_B": {
            "reputation_score": 0.30,
            "vehicle_capacity": {"type": "scooter", "vol_cap_l": 60, "weight_cap_kg": 30},
            "special_equipment": {"insulated_container": False}, # Courier B lacks the container
            "status": "stuck",
            "location": (40.7306, -73.9995)
        },
        "courier_C": {
            "reputation_score": 0.95,
            "vehicle_capacity": {"type": "car", "vol_cap_l": 250, "weight_cap_kg": 100},
            "special_equipment": {"insulated_container": True}, # Courier C has the container
            "status": "available",
            "location": (40.7580, -73.9855)
        }
    },
    "weather_service": {
        "New York": {
            "alert": "severe_rain_warning",
            "reroute_required": True
        },
        "Los Angeles": {
            "alert": "none",
            "reroute_required": False
        }
    },
    "merchants": {
        "M123": {
            "health": "HEALTHY",
            "prep_eta_min": 14,
            "oos_items": []
        },
        "M456": {
            "health": "OFFLINE",
            "prep_eta_min": 0,
            "oos_items": []
        }
    },
    "promotions": {
    "PERISHABLE_PROMO": {
        "active": True,
        "type": "geo_fenced",
        "valid_merchants": ["M123"] # Assuming M123 is a perishable food merchant
    }
},
}

ORDER_ITEMS_DATA: Dict[str, Any] = {
    "order_10000": {
        "items": [
            {"sku": "MILK-1L", "qty": 1, "vol_l": 1.0, "weight_kg": 1.0, "is_bulky": False},
            {"sku": "BREAD", "qty": 1, "vol_l": 2.0, "weight_kg": 0.5, "is_bulky": False},
            {"sku": "WATER-20L", "qty": 1, "vol_l": 20.0, "weight_kg": 20.0, "is_bulky": True}
        ]
    },
    "order_20000": {
        "items": [
            {"sku": "SUSHI-ROLL", "qty": 1, "vol_l": 0.5, "weight_kg": 0.5, "is_bulky": False, "item_type": "perishable"},
            {"sku": "ICE-CREAM-PINT", "qty": 1, "vol_l": 0.5, "weight_kg": 0.5, "is_bulky": False, "item_type": "perishable"}
        ]
    }
}