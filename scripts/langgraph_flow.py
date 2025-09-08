from __future__ import annotations
from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from pydantic import ConfigDict
from langchain_core.tools import Tool

# ---- Bring your models & tools ----
from scripts.core_datastructures import (
    AgentState, AgentReturnEnvelope,
    PaymentAgentInput, ReputationAgentInput, CourierBreakdownInput,
    CapacityAgentInput, SplitDeliveryInput, WeatherAgentInput,
    MerchantStatusInput, DeliveryDispatchInput, RerouteInput,
    CustomerChangeInput, PolicyGuardInput, NotifyAgentInput, AuditAgentInput,
    PolicyStatus, NotificationEvent
)
from scripts.tools import (
    payment_agent, reputation_agent, courier_breakdown_agent, capacity_agent,
    split_delivery_agent, weather_agent, merchant_status_agent, delivery_dispatch_agent,
    reroute_agent, customer_change_agent, policy_guard, notify_agent, audit_agent
)


# =========================================================
# 1) Helpers
# =========================================================

def _merge_envelope(state: AgentState, env: Dict[str, Any], thought: Optional[str] = None) -> AgentState:
    """
    Merge a tool's envelope (dict) into the AgentState.
    - updates -> state.order_details (deep merge, shallow per key)
    - signals -> state.order_details["signals"]
    - metrics -> append into audit_log entry
    - reason -> appended to audit_log / thoughts
    """
    # Validate/normalize state on entry (safe, optional)
    state = AgentState.model_validate(state)

    updates: Dict[str, Any] = env.get("updates", {}) or {}
    signals: Dict[str, Any] = env.get("signals", {}) or {}
    metrics: Dict[str, Any] = env.get("metrics", {}) or {}
    reason: Optional[str] = env.get("reason")

    # Merge updates (shallow per top key)
    for k, v in updates.items():
        # keep existing dicts merged shallowly
        if isinstance(v, dict) and isinstance(state.order_details.get(k), dict):
            state.order_details[k].update(v)
        else:
            state.order_details[k] = v

    # Store/merge signals in a dedicated place for router
    sd = state.order_details.get("signals", {})
    if not isinstance(sd, dict):
        sd = {}
    sd.update(signals)
    state.order_details["signals"] = sd

    # Append to audit_log
    log_entry = {
        "reason": reason,
        "signals": signals,
        "metrics": metrics,
        "updates_keys": list(updates.keys())
    }
    if thought:
        log_entry["thought"] = thought
    state.audit_log.append(log_entry)

    return state


def _get_signal(state: AgentState, key: str, default: Any = False) -> Any:
    sigs = state.order_details.get("signals", {}) or {}
    return sigs.get(key, default)


# =========================================================
# 2) Nodes (one thin wrapper per tool)
#    Each node:
#      - builds kwargs from state
#      - calls the tool (which validates with args_schema)
#      - merges the envelope into state
# =========================================================

def node_payment(state: AgentState) -> AgentState:
    order = state.order_details
    # Build tool inputs (Your PaymentAgentInput expects: payment, order_total, user_prefs)
    kwargs = {
        "payment": order.get("payment", {}),
        "order_total": order.get("order_total", 0.0),
        "user_prefs": order.get("user_prefs", {})
    }
    env = payment_agent.invoke(kwargs)  # returns dict
    return _merge_envelope(state, env, thought="Payment check")

def node_merchant(state: AgentState) -> AgentState:
    order = state.order_details
    kwargs = {
        "merchant_id": order.get("merchant_id"),
        "items": order.get("items", [])
    }
    env = merchant_status_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Merchant status & stock")

def node_dispatch(state: AgentState) -> AgentState:
    order = state.order_details
    kwargs = {
        "pickup_location": order.get("pickup_location", {}),
        "drop_location": order.get("drop_location", {}),
        "readiness_eta_min": order.get("readiness_eta_min", 0),
        "priority_flag": bool(order.get("priority_flag", False))
    }
    env = delivery_dispatch_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Courier dispatch")

def node_reputation(state: AgentState) -> AgentState:
    order = state.order_details
    courier_id = (order.get("courier") or {}).get("id")
    kwargs = {
        "courier_candidate_id": courier_id,
        "historical_kpis": order.get("historical_kpis", {})
    }
    env = reputation_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Courier reputation gate")

def node_capacity(state: AgentState) -> AgentState:
    order = state.order_details
    courier_id = (order.get("courier") or {}).get("id")
    kwargs = {
        "order_id": order.get("order_id"),
        "courier_id": courier_id
    }
    env = capacity_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Capacity check")

def node_split(state: AgentState) -> AgentState:
    order = state.order_details
    kwargs = {
        "order_id": order.get("order_id"),
        "customer_response": (order.get("customer_response") or "disagree"),
        "overflow_items": (order.get("capacity") or {}).get("overflow_items", []),
        "courier_pool": order.get("courier_pool", []),
        "policy_split_rules": order.get("policy_split_rules", {}),
        "user_prefs": order.get("user_prefs", {})
    }
    env = split_delivery_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Split delivery negotiation")

def node_weather(state: AgentState) -> AgentState:
    order = state.order_details
    kwargs = {
        "courier_location": order.get("pickup_location", {}).get("city", "Unknown"),
        "destination_city": order.get("drop_location", {}).get("city", "Unknown")
    }
    env = weather_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Weather check")

def node_breakdown(state: AgentState) -> AgentState:
    order = state.order_details
    kwargs = {
        "courier_id": (order.get("courier") or {}).get("id"),
        "telemetry": order.get("telemetry", {}),
        "route": order.get("route", {})
    }
    env = courier_breakdown_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Breakdown/idle detection")

def node_reroute(state: AgentState) -> AgentState:
    order = state.order_details
    kwargs = {
        "reason": order.get("reroute_reason", "risk"),
        "current_courier": (order.get("courier") or {}).get("id"),
        "candidate_pool": order.get("candidate_pool", []),
        "weather_advice": (order.get("weather") or {}).get("advice")
    }
    env = reroute_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Reroute / reassignment")

def node_customer_change(state: AgentState) -> AgentState:
    order = state.order_details
    kwargs = {
        "request": order.get("customer_change_request", {}),
        "courier_position": order.get("courier_position", {}),
        "policy_change_rules": order.get("policy_change_rules", {})
    }
    env = customer_change_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Customer-initiated change")

def _as_float(x, default=0.0) -> float:
    # Accept number, numeric string, or dicts like {"wallet_delta": 249.0, "balance": ...}
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            return default
    if isinstance(x, dict):
        # common keys we might set from upstream tools
        for k in ("wallet_delta", "credit_delta", "amount", "balance", "value"):
            if k in x and isinstance(x[k], (int, float, str)):
                try:
                    return float(x[k])
                except ValueError:
                    pass
        return default
    return default

def node_policy(state: AgentState) -> AgentState:
    order = state.order_details
    eta_min = (order.get("route") or {}).get("eta_min", 0)

    kwargs = {
        "eta_min": int(eta_min),
        "sla_eta_min": int(order.get("sla_eta_min", 30)),
        "price_delta": _as_float(order.get("price_delta", 0.0), 0.0),
        "credits": _as_float(order.get("credits", 0.0), 0.0),     # <-- robust
        "split_plan": order.get("split_plan", {}) or {},
        "change_fees": _as_float(order.get("change_fees", 0.0), 0.0),
    }
    env = policy_guard.invoke(kwargs)
    return _merge_envelope(state, env, thought="Policy / SLA validation")

# def node_policy(state: AgentState) -> AgentState:
#     order = state.order_details
#     # Compose inputs for PolicyGuard from order_details
#     kwargs = {
#         "eta_min": (order.get("route") or {}).get("eta_min", 0),
#         "sla_eta_min": order.get("sla_eta_min", 30),
#         "price_delta": float(order.get("price_delta", 0.0)),
#         "credits": float(order.get("credits", 0.0)),
#         "split_plan": order.get("split_plan", {}),
#         "change_fees": float(order.get("change_fees", 0.0)),
#     }
#     env = policy_guard.invoke(kwargs)
#     return _merge_envelope(state, env, thought="Policy / SLA validation")

def node_notify(state: AgentState) -> AgentState:
    order = state.order_details
    # Decide event by context (simple example)
    event = order.get("notify_event") or NotificationEvent.delivered
    kwargs = {
        "event": event,
        "payload": order.get("notify_payload", {}),
        "target": order.get("notify_targets", ["user", "merchant"])
    }
    env = notify_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Notify stakeholders")

def node_audit(state: AgentState) -> AgentState:
    order = state.order_details

    # Build human-readable thoughts from reasons
    thoughts = [e.get("reason") for e in state.audit_log if e.get("reason")]

    # Convert updates_keys (which is a list) into a single string per event
    def _event_label(entry: dict) -> str:
        keys = entry.get("updates_keys", [])
        if isinstance(keys, list):
            return ",".join(map(str, keys)) if keys else "none"
        return str(keys) if keys is not None else "none"

    events = [_event_label(e) for e in state.audit_log]

    kwargs = {
        "thoughts": thoughts,
        "events": events,            # <-- now List[str]
        "state_diff": order
    }
    env = audit_agent.invoke(kwargs)
    return _merge_envelope(state, env, thought="Persist audit trace")



# =========================================================
# 3) Router
#    Read signals from state.order_details["signals"] and decide next node
# =========================================================

def router(state: AgentState) -> str:
    sig = state.order_details.get("signals", {}) or {}

    # After Payment -> Merchant
    if not state.order_details.get("_phase"):
        return "payment"

    phase = state.order_details["_phase"]

    if phase == "payment":
        return "merchant"

    if phase == "merchant":
        return "dispatch" if not sig.get("needs_alt_sourcing") else "notify"

    if phase == "dispatch":
        return "reputation" if sig.get("on_route") else "notify"

    if phase == "reputation":
        return "reroute" if sig.get("reassign_courier") else "capacity"

    if phase == "capacity":
        return "split" if sig.get("propose_split_delivery") else "weather"

    if phase == "split":
        # spawn_second_dispatch or find_new_courier both eventually continue
        return "weather"

    if phase == "weather":
        return "reroute" if sig.get("require_reroute") else "breakdown"

    if phase == "breakdown":
        return "reroute" if sig.get("need_backup_courier") else "customer_change"

    if phase == "reroute":
        return "customer_change" if sig.get("reroute_done") else "notify"

    if phase == "customer_change":
        return "policy"  # regardless, we proceed to guard

    if phase == "policy":
        return "notify"  # proceed or warn, we notify

    if phase == "notify":
        return "audit"

    if phase == "audit":
        return END

    # default
    return END


# =========================================================
# 4) Build Graph
# =========================================================

def build_graph():
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("payment", _phase_wrapper("payment", node_payment))
    graph.add_node("merchant", _phase_wrapper("merchant", node_merchant))
    graph.add_node("dispatch", _phase_wrapper("dispatch", node_dispatch))
    graph.add_node("reputation", _phase_wrapper("reputation", node_reputation))
    graph.add_node("capacity", _phase_wrapper("capacity", node_capacity))
    graph.add_node("split", _phase_wrapper("split", node_split))
    graph.add_node("weather", _phase_wrapper("weather", node_weather))
    graph.add_node("breakdown", _phase_wrapper("breakdown", node_breakdown))
    graph.add_node("reroute", _phase_wrapper("reroute", node_reroute))
    graph.add_node("customer_change", _phase_wrapper("customer_change", node_customer_change))
    graph.add_node("policy", _phase_wrapper("policy", node_policy))
    graph.add_node("notify", _phase_wrapper("notify", node_notify))
    graph.add_node("audit", _phase_wrapper("audit", node_audit))

    # Router edges (single dynamic router)
    graph.set_entry_point("payment")
    graph.add_edge("payment", "merchant")
    graph.add_conditional_edges("merchant", router, {
        "dispatch": "dispatch",
        "notify": "notify",
        END: END
    })
    graph.add_conditional_edges("dispatch", router, {
        "reputation": "reputation",
        "notify": "notify",
        END: END
    })
    graph.add_conditional_edges("reputation", router, {
        "reroute": "reroute",
        "capacity": "capacity",
        END: END
    })
    graph.add_conditional_edges("capacity", router, {
        "split": "split",
        "weather": "weather",
        END: END
    })
    graph.add_conditional_edges("split", router, {
        "weather": "weather",
        END: END
    })
    graph.add_conditional_edges("weather", router, {
        "reroute": "reroute",
        "breakdown": "breakdown",
        END: END
    })
    graph.add_conditional_edges("breakdown", router, {
        "reroute": "reroute",
        "customer_change": "customer_change",
        END: END
    })
    graph.add_conditional_edges("reroute", router, {
        "customer_change": "customer_change",
        "notify": "notify",
        END: END
    })
    graph.add_conditional_edges("customer_change", router, {
        "policy": "policy",
        END: END
    })
    graph.add_conditional_edges("policy", router, {
        "notify": "notify",
        END: END
    })
    graph.add_conditional_edges("notify", router, {
        "audit": "audit",
        END: END
    })
    # audit -> END implicitly via router
    graph.add_conditional_edges("audit", router, {
        END: END
    })

    return graph.compile()

def _phase_wrapper(phase_name: str, fn):
    """
    Decorator to mark current phase in the state before executing node.
    Ensures router knows where we are.
    """
    def wrapped(state: Dict[str, Any]) -> Dict[str, Any]:
        # Validate/normalize and set phase
        st = AgentState.model_validate(state)
        st.order_details["_phase"] = phase_name
        st = fn(st)
        return st.model_dump()
    return wrapped


# =========================================================
# 5) Minimal Demo
# =========================================================
if __name__ == "__main__":
    app = build_graph()
    initial_state = AgentState(
        messages=[],
        order_details={
            "order_id": "order_12345",
            "merchant_id": "M123",
            "items": [
                {"sku": "MILK-1L", "qty": 1, "vol_l": 1.0, "is_bulky": False},
                {"sku": "BREAD", "qty": 1, "vol_l": 2.0, "is_bulky": False},
                {"sku": "WATER-20L", "qty": 1, "vol_l": 20.0, "is_bulky": True}
            ],
            "payment": {"transactions": [{"id": "t1"}]},
            "order_total": 249.0,
            "user_prefs": {"payment_priority": "wallet"},
            "pickup_location": {"lat": 40.73, "lng": -73.99, "city": "New York"},
            "drop_location": {"lat": 40.76, "lng": -73.98, "city": "New York"},
            "readiness_eta_min": 5,
            "priority_flag": True,

            # Optional extras used by some nodes
            "sla_eta_min": 30,
            "credits": 50.0,
            "price_delta": 0.0,
            "change_fees": 0.0,
            "customer_response": "agree",
            "customer_change_request": {"type": "payment", "payload": {}},
            "policy_change_rules": {"cutoff_min": 10, "max_km_address_change": 5, "fee_flat": 0.0},
            "telemetry": {"sos_flag": False, "speed": 20},
        },
        audit_log=[]
    )

    final_state = app.invoke(initial_state.model_dump())
    # Pretty-print result
    import json
    print(json.dumps(final_state["order_details"], indent=2))
