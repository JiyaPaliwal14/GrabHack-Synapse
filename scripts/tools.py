from langchain_core.tools import tool
from typing import TypedDict, Annotated, List, Dict, Any
import time

# Let's import the mock data and return envelope from our other files.
# In a real project, you would import these from the files you created earlier.
from core_datastructures import CommonReturnEnvelope
from dataset.mock_data import MOCK_DATABASE, ORDER_ITEMS_DATA


# This tool detects a double-charge and simulates an automated refund.
@tool
def payment_agent(order_id: str) -> CommonReturnEnvelope:
    """
    Detects if a payment was charged twice for an order and initiates an auto-refund.
    This tool should be called at the beginning of an order's lifecycle.
    
    :param order_id: The ID of the order to check.
    :return: A CommonReturnEnvelope with the outcome.
    """
    start_time = time.time()
    order_txns = MOCK_DATABASE["payment_gateway"].get(order_id, {}).get("transactions", [])
    
    if len(order_txns) > 1:
        # Simulates refunding the second charge.
        new_transaction = {"id": "tx_refund_xyz", "amount": 25.50, "status": "refunded"}
        MOCK_DATABASE["payment_gateway"][order_id]["transactions"].append(new_transaction)
        
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Detected double charge for {order_id}. Auto-refund initiated.",
            updates={"payment_status": "refund_in_progress", "total_transactions": len(order_txns)},
            signals={"issue_detected": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
    else:
        return CommonReturnEnvelope(
            ok=True,
            reason="No double charge detected.",
            updates={},
            signals={},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )

# This tool checks a courier's reputation and signals if they are a risk.
@tool
def reputation_agent(courier_id: str) -> CommonReturnEnvelope:
    """
    Checks the reputation score of a courier and signals if their score is too low.
    
    :param courier_id: The ID of the courier to check.
    :return: A CommonReturnEnvelope with the outcome.
    """
    start_time = time.time()
    courier_data = MOCK_DATABASE["couriers"].get(courier_id, {})
    
    if courier_data.get("reputation_score", 1.0) < 0.5:
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Courier {courier_id} has a low reputation score. Reassignment recommended.",
            updates={"risk_level": "high", "courier_id": "reassigned"},
            signals={"reassign_courier": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
    else:
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Courier {courier_id} has an acceptable reputation score.",
            updates={"risk_level": "low"},
            signals={},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )

# This tool detects if a courier is stuck or has broken down.
@tool
def courier_breakdown_agent(courier_id: str) -> CommonReturnEnvelope:
    """
    Detects if a courier has been idle for too long or sent an SOS.
    
    :param courier_id: The ID of the courier to check.
    :return: A CommonReturnEnvelope with the outcome.
    """
    start_time = time.time()
    # Mocking a breakdown scenario.
    is_stuck = MOCK_DATABASE["couriers"].get(courier_id, {}).get("status") == "stuck"
    
    if is_stuck:
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Courier {courier_id} has broken down. Finding a backup courier.",
            updates={"courier_status": "broken_down"},
            signals={"find_backup_courier": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
    else:
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Courier {courier_id} is en route without issues.",
            updates={"courier_status": "en_route"},
            signals={},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )

# This tool checks if an order can fit in a courier's vehicle.
@tool
def capacity_agent(courier_id: str, order_id: str) -> CommonReturnEnvelope:
    """
    Checks if a courier's vehicle has enough capacity for all order items.
    
    :param courier_id: The ID of the courier.
    :param order_id: The ID of the order.
    :return: A CommonReturnEnvelope with the outcome.
    """
    start_time = time.time()
    courier_capacity = MOCK_DATABASE["couriers"].get(courier_id, {}).get("vehicle_capacity")
    order_items = ORDER_ITEMS_DATA.get(order_id, {}).get("items", [])
    
    has_bulky_item = any(item["size"] == "bulky" for item in order_items)
    
    if courier_capacity == "small" and has_bulky_item:
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Courier {courier_id}'s small vehicle cannot fit a bulky item.",
            updates={"delivery_status": "capacity_issue"},
            signals={"split_delivery_needed": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
    else:
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Order fits within courier {courier_id}'s vehicle capacity.",
            updates={"delivery_status": "capacity_ok"},
            signals={},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
        
# This tool handles splitting a delivery and getting customer approval.
@tool
def split_delivery_agent(order_id: str, customer_response: str) -> CommonReturnEnvelope:
    """
    Negotiates a split delivery with the customer.
    
    :param order_id: The ID of the order.
    :param customer_response: The customer's response to the split delivery proposal (e.g., 'agree' or 'disagree').
    :return: A CommonReturnEnvelope with the outcome.
    """
    start_time = time.time()
    if customer_response.lower() == "agree":
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Customer agreed to split delivery. Creating two separate deliveries.",
            updates={"delivery_plan": "split", "first_delivery_items": ["item_1", "item_2"], "second_delivery_items": ["item_3"]},
            signals={"split_successful": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
    else:
        return CommonReturnEnvelope(
            ok=True,
            reason="Customer declined split delivery. Finding a new courier.",
            updates={"delivery_plan": "single"},
            signals={"find_new_courier": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )

# This tool checks for weather alerts and reroutes the delivery.
@tool
def weather_agent(courier_location: str, destination_city: str) -> CommonReturnEnvelope:
    """
    Checks for sudden weather alerts and determines if a reroute is needed.
    
    :param courier_location: The current location of the courier.
    :param destination_city: The destination city for the delivery.
    :return: A CommonReturnEnvelope with the outcome.
    """
    start_time = time.time()
    weather_info = MOCK_DATABASE["weather_service"].get(destination_city, {})
    
    if weather_info.get("reroute_required"):
        # Simulates a new route being calculated
        new_route = "Route via I-95 South"
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Weather alert detected in {destination_city}. Rerouting delivery.",
            updates={"route_status": "rerouted", "current_route": new_route},
            signals={"reroute_needed": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
    else:
        return CommonReturnEnvelope(
            ok=True,
            reason=f"Weather is clear in {destination_city}. No reroute required.",
            updates={"route_status": "on_track"},
            signals={},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )