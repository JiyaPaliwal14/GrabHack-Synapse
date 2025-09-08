from langchain_core.tools import tool
import time
from typing import Dict, List, Optional, Any
from pydantic import ValidationError

# replace the relative imports with absolute, sibling imports
from scripts.core_datastructures import (
    AgentReturnEnvelope, ContainerAgentInput, PaymentAgentInput, PromotionGuardInput, ReputationAgentInput,
    CourierBreakdownInput, CapacityAgentInput, SplitDeliveryInput,
    WeatherAgentInput, MerchantStatusInput, DeliveryDispatchInput,
    RerouteInput, CustomerChangeInput, PolicyGuardInput, NotifyAgentInput,
    AuditAgentInput, MerchantHealth, PolicyStatus, ActionType, NotificationEvent
)
from dataset.mock_data import MOCK_DATABASE, ORDER_ITEMS_DATA


# Helper function to validate inputs and handle errors
def _safe_call(func, inputs):
    try:
        validated_inputs = inputs.__class__(**inputs.dict())
        return func(validated_inputs)
    except ValidationError as e:
        return AgentReturnEnvelope(
            ok=False,
            reason=f"Input validation failed: {e}",
            updates={},
            signals={},
            metrics={}
        )

# 1) PaymentAgent
@tool(args_schema=PaymentAgentInput)
def payment_agent(**kwargs) -> dict:
    """Detects double charges, resolves holds, switches payment method, computes refunds/credits."""
    start_time = time.time()
    inputs = PaymentAgentInput(**kwargs)
    if len(inputs.payment.get("transactions", [])) > 1:
        return AgentReturnEnvelope(
            ok=True,
            reason="Detected and resolved double charge.",
            updates={
                "payment": {
                    "double_charge": True,
                    "refunds": [{"txn_id": "TX_REFUND_1", "amount": inputs.order_total, "to": inputs.user_prefs.get("payment_priority")}],
                    "status": "REFUNDED"
                },
                "credits": {"wallet_delta": inputs.order_total}
            },
            signals={"payment_fixed": True, "needs_user_action": False},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    return AgentReturnEnvelope(
        ok=True,
        reason="No double charge detected.",
        updates={"payment": {"double_charge": False, "status": "OK"}},
        signals={"payment_fixed": True},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 2) ReputationAgent
@tool(args_schema=ReputationAgentInput)
def reputation_agent(**kwargs) -> dict:
    """Scores courier risk and decides if reassignment is safer."""
    start_time = time.time()
    inputs = ReputationAgentInput(**kwargs)
    score = MOCK_DATABASE["couriers"].get(inputs.courier_candidate_id, {}).get("reputation_score", 0)
    
    if score < 0.5:
        return AgentReturnEnvelope(
            ok=True,
            reason="Courier flagged due to low reputation score.",
            updates={"risk": {"courier_id": inputs.courier_candidate_id, "score": score, "label": "HIGH", "recommend_reassign": True}},
            signals={"reassign_courier": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    return AgentReturnEnvelope(
        ok=True,
        reason="Courier has an acceptable reputation score.",
        updates={"risk": {"courier_id": inputs.courier_candidate_id, "score": score, "label": "LOW", "recommend_reassign": False}},
        signals={"reassign_courier": False},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 3) CourierBreakdownAgent
@tool(args_schema=CourierBreakdownInput)
def courier_breakdown_agent(**kwargs) -> dict:
    """Detects breakdowns/immobility (driver SOS, long idle)."""
    start_time = time.time()
    inputs = CourierBreakdownInput(**kwargs)
    if inputs.telemetry.get("sos_flag") or inputs.telemetry.get("speed") == 0 and inputs.route.get("progress") < 1.0:
        return AgentReturnEnvelope(
            ok=True,
            reason="SOS signal and zero speed detected.",
            updates={"breakdown": {"detected": True, "reason": "vehicle_breakdown", "since_sec": 120}},
            signals={"need_backup_courier": True, "pause_eta_updates": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    return AgentReturnEnvelope(
        ok=True,
        reason="Courier is en route without issues.",
        updates={"breakdown": {"detected": False}},
        signals={},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 4) CapacityAgent
@tool(args_schema=CapacityAgentInput)
def capacity_agent(**kwargs) -> dict:
    """Checks if a courier’s vehicle can carry the full order; computes overflow."""
    start_time = time.time()
    inputs = CapacityAgentInput(**kwargs)
    order_items = ORDER_ITEMS_DATA.get(inputs.order_id, {}).get("items", [])
    courier_vehicle = MOCK_DATABASE["couriers"].get(inputs.courier_id, {}).get("vehicle_capacity", {})
    
    total_vol = sum(item["vol_l"] for item in order_items)
    
    if total_vol > courier_vehicle.get("vol_cap_l", 0) or any(item.get("is_bulky") for item in order_items):
        return AgentReturnEnvelope(
            ok=True,
            reason="Order contains items that exceed vehicle capacity.",
            updates={"capacity": {"fits": False, "fit_ratio": total_vol / courier_vehicle.get("vol_cap_l"), "overflow_items": [i['sku'] for i in order_items if i.get('is_bulky')]}},
            signals={"propose_split_delivery": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    return AgentReturnEnvelope(
        ok=True,
        reason="All items fit within vehicle capacity.",
        updates={"capacity": {"fits": True, "fit_ratio": 1.0, "overflow_items": []}},
        signals={},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 5) SplitDeliveryAgent
@tool(args_schema=SplitDeliveryInput)
def split_delivery_agent(**kwargs) -> dict:
    """Negotiates partial-now / later delivery, computes ETAs & fees/waivers."""
    start_time = time.time()
    inputs = SplitDeliveryInput(**kwargs)
    if inputs.customer_response.lower() == "agree":
        now_items = [item for item in ORDER_ITEMS_DATA.get(inputs.order_id, {}).get("items", []) if not item.get("is_bulky")]
        later_items = [item for item in ORDER_ITEMS_DATA.get(inputs.order_id, {}).get("items", []) if item.get("is_bulky")]
        
        return AgentReturnEnvelope(
            ok=True,
            reason="Customer agreed to split delivery.",
            updates={"split_plan": {"accepted": True, "now_items": [i['sku'] for i in now_items], "later_items": [i['sku'] for i in later_items], "later_eta_min": 120, "fee": 0.0, "waiver_applied": True}},
            signals={"spawn_second_dispatch": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    return AgentReturnEnvelope(
        ok=True,
        reason="Customer declined split delivery.",
        updates={"split_plan": {"accepted": False}},
        signals={"find_new_courier": True},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 6) WeatherAgent
@tool(args_schema=WeatherAgentInput)
def weather_agent(**kwargs) -> dict:
    """Pulls weather alerts and adjusts route cost/ETA."""
    start_time = time.time()
    inputs = WeatherAgentInput(**kwargs)
    weather_info = MOCK_DATABASE["weather_service"].get(inputs.destination_city, {})
    
    if weather_info.get("reroute_required"):
        return AgentReturnEnvelope(
            ok=True,
            reason=f"Weather alert detected in {inputs.destination_city}.",
            updates={"weather": {"alert": "RAIN_HEAVY", "severity": "HIGH", "eta_penalty_min": 7, "advice": "avoid_underpass"}},
            signals={"require_reroute": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    return AgentReturnEnvelope(
        ok=True,
        reason="Weather is clear. No reroute required.",
        updates={"weather": {"alert": "NONE"}},
        signals={},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 7) MerchantStatusAgent
@tool(args_schema=MerchantStatusInput)
def merchant_status_agent(**kwargs) -> dict:
    """Checks merchant health and item stock."""
    start_time = time.time()
    inputs = MerchantStatusInput(**kwargs)
    merchant_data = MOCK_DATABASE["merchants"].get(inputs.merchant_id, {})

    if merchant_data.get("health") == "HEALTHY":
        return AgentReturnEnvelope(
            ok=True,
            reason="Merchant is healthy and stock is confirmed.",
            updates={"merchant": {"health": MerchantHealth.healthy, "prep_eta_min": 14, "oos_items": []}},
            signals={"needs_alt_sourcing": False},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    else:
        return AgentReturnEnvelope(
            ok=True,
            reason="Merchant is temporarily offline.",
            updates={"merchant": {"health": MerchantHealth.offline, "prep_eta_min": 0, "oos_items": []}},
            signals={"needs_alt_sourcing": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()

# 8) DeliveryDispatchAgent
@tool(args_schema=DeliveryDispatchInput)
def delivery_dispatch_agent(**kwargs) -> dict:
    """Assigns a courier and initial route/ETA."""
    start_time = time.time()
    inputs = DeliveryDispatchInput(**kwargs)
    courier_id = "courier_B" # Simulate assigning a low-rep courier
    courier_data = MOCK_DATABASE["couriers"][courier_id]
    
    return AgentReturnEnvelope(
        ok=True,
        reason=f"Courier {courier_id} assigned and route calculated.",
        updates={
            "courier": {"id": courier_id, "vehicle": courier_data.get("vehicle_capacity"), "rating": courier_data.get("reputation_score")},
            "route": {"polyline": "ENCODED_POLYLINE_STRING", "eta_min": 22}
        },
        signals={"on_route": True},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 9) RerouteAgent
@tool(args_schema=RerouteInput)
def reroute_agent(**kwargs) -> dict:
    """Picks a better courier or route when a delay/risk arises."""
    start_time = time.time()
    inputs = RerouteInput(**kwargs)
    if inputs.reason == "risk":
        new_courier_id = "courier_C" # Simulate reassigning to a high-rep courier
        return AgentReturnEnvelope(
            ok=True,
            reason=f"Rerouting due to courier risk. Reassigning to {new_courier_id}.",
            updates={"reroute": {"action": ActionType.reassign, "new_courier_id": new_courier_id, "eta_min": 19}},
            signals={"reroute_done": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    elif inputs.reason == "weather":
        return AgentReturnEnvelope(
            ok=True,
            reason=f"Rerouting to avoid bad weather.",
            updates={"reroute": {"action": ActionType.route_replan, "new_courier_id": inputs.current_courier, "eta_min": 25}},
            signals={"reroute_done": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    
    return AgentReturnEnvelope(
        ok=False,
        reason="Reroute reason not recognized.",
        updates={},
        signals={},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 10) CustomerChangeAgent
@tool
def customer_change_agent(inputs: CustomerChangeInput) -> AgentReturnEnvelope:
    """Applies user-initiated changes mid-route, like address or payment modes."""
    start_time = time.time()

    if inputs.request.get("type") == "address_change":
        new_address = inputs.request.get("new_address", {})
        # Simulate a quick feasibility check based on distance
        current_courier_loc = inputs.courier_position
        new_dist_km = ((new_address.get('lat', 0) - current_courier_loc.get('lat', 0))**2 + (new_address.get('lon', 0) - current_courier_loc.get('lon', 0))**2)**0.5 * 100

        if new_dist_km < 10:
            return AgentReturnEnvelope(
                ok=True,
                reason="Address change is feasible. Rerouting now.",
                updates={"customer_change": {"type": "address", "feasible": True, "new_eta_min": inputs.eta_min + int(new_dist_km * 2), "fee": 0.0}},
                signals={"require_reroute": True},
                metrics={"latency_ms": (time.time() - start_time) * 1000}
            )
        else:
            return AgentReturnEnvelope(
                ok=False,
                reason="Address change is too far and not feasible.",
                updates={"customer_change": {"type": "address", "feasible": False}},
                signals={},
                metrics={"latency_ms": (time.time() - start_time) * 1000}
            )

    if inputs.request.get("type") == "payment":
        return AgentReturnEnvelope(
            ok=True,
            reason="Payment method change is feasible.",
            updates={"customer_change": {"type": "payment", "feasible": True, "eta_min": 0, "fee": 0.0}},
            signals={"notify_user": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )

    return AgentReturnEnvelope(
        ok=False,
        reason="Change request is not recognized or feasible.",
        updates={},
        signals={},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    )

# 11) PolicyGuard
@tool(args_schema=PolicyGuardInput)
def policy_guard(**kwargs) -> dict:
    """Validates final plan against SLA and compliance."""
    start_time = time.time()
    inputs = PolicyGuardInput(**kwargs)
    if inputs.eta_min > inputs.sla_eta_min:
        return AgentReturnEnvelope(
            ok=True,
            reason="Order ETA exceeds SLA. Applying credit.",
            updates={"policy": {"status": PolicyStatus.warn, "violations": ["SLA_VIOLATION"], "fallback": "CREDIT_WAIVER"}},
            signals={"proceed": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        ).model_dump()
    
    return AgentReturnEnvelope(
        ok=True,
        reason="Plan is compliant with all policies.",
        updates={"policy": {"status": PolicyStatus.ok, "violations": [], "fallback": None}},
        signals={"proceed": True},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 12) NotifyAgent
@tool(args_schema=NotifyAgentInput)
def notify_agent(**kwargs) -> dict:
    """Composes and sends notifications to users, merchants, or couriers."""
    start_time = time.time()
    inputs = NotifyAgentInput(**kwargs)
    message_map = {
        NotificationEvent.refund: "Refund of ${payload[amount]} has been processed to your wallet.",
        NotificationEvent.split_confirmed: "Your order will be delivered in two parts. Essentials coming soon, bulky item later.",
        NotificationEvent.delivered: "Your order has been successfully delivered.",
        NotificationEvent.customer_change: "Your payment method has been successfully updated."
    }
    
    message_template = message_map.get(inputs.event, "Update on your order.")
    final_message = message_template.format(payload=inputs.payload)
    
    return AgentReturnEnvelope(
        ok=True,
        reason=f"Notification sent for event: {inputs.event.value}.",
        updates={"notify": {"sent_to": inputs.target, "channels": ["push", "sms"], "message": final_message}},
        signals={"notified": True},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()

# 13) AuditAgent
@tool(args_schema=AuditAgentInput)
def audit_agent(**kwargs) -> dict:
    """Persists all thoughts, decisions, and metrics, and a compact reasoning summary."""
    start_time = time.time()
    inputs = AuditAgentInput(**kwargs)
    summary = " → ".join(inputs.thoughts)
    return AgentReturnEnvelope(
        ok=True,
        reason="Audit log successfully saved.",
        updates={"audit": {"saved": True, "trace_id": f"TRC-{int(time.time())}", "summary": summary}},
        signals={"trace_complete": True},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    ).model_dump()
   
    
@tool
def container_agent(inputs: ContainerAgentInput) -> AgentReturnEnvelope:
    """Checks if a courier's vehicle is equipped with specialized containers."""
    start_time = time.time()
    courier_data = MOCK_DATABASE["couriers"].get(inputs.courier_id, {})

    if inputs.item_type == "perishable" and not courier_data.get("special_equipment", {}).get("insulated_container"):
        return AgentReturnEnvelope(
            ok=True,
            reason="Courier lacks the insulated container for perishable items.",
            updates={"equipment": {"has_container": False, "required": True}},
            signals={"needs_new_courier": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
    return AgentReturnEnvelope(
        ok=True,
        reason="Courier is properly equipped for this delivery.",
        updates={"equipment": {"has_container": True, "required": True}},
        signals={},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    )
    
@tool
def promotion_guard(inputs: PromotionGuardInput) -> AgentReturnEnvelope:
    """Validates if a proposed reroute or change violates an active promotion."""
    start_time = time.time()

    if inputs.promotion_code == "PERISHABLE_PROMO" and inputs.proposed_action != "stay_on_route":
        return AgentReturnEnvelope(
            ok=True,
            reason=f"Proposed action '{inputs.proposed_action}' violates promotion {inputs.promotion_code}.",
            updates={"policy": {"status": "WARN", "violations": ["PROMOTION_VIOLATION"]}},
            signals={"cancel_reroute_to_avoid_penalty": True},
            metrics={"latency_ms": (time.time() - start_time) * 1000}
        )
    return AgentReturnEnvelope(
        ok=True,
        reason="Proposed action does not violate any active promotions.",
        updates={"policy": {"status": "OK", "violations": []}},
        signals={},
        metrics={"latency_ms": (time.time() - start_time) * 1000}
    )

