from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, conlist
from enum import Enum
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# --- Common Models ---
class AgentReturnEnvelope(BaseModel):
    """The common return envelope for all agents."""
    ok: bool
    reason: Optional[str] = None
    updates: Dict[str, Any] = Field(default_factory=dict)
    signals: Dict[str, bool] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)

# --- Helper Enums ---
class VehicleType(str, Enum):
    bike = "bike"
    scooter = "scooter"
    car = "car"
    van = "van"

class MerchantHealth(str, Enum):
    healthy = "HEALTHY"
    soft_blackout = "SOFT_BLACKOUT"
    offline = "OFFLINE"

class PolicyStatus(str, Enum):
    ok = "OK"
    block = "BLOCK"
    warn = "WARN"

class ActionType(str, Enum):
    reassign = "REASSIGN"
    waypoint_change = "WAYPOINT_CHANGE"
    route_replan = "ROUTE_REPLAN"

class NotificationEvent(str, Enum):
    offer = "OFFER"
    reroute = "REROUTE"
    split_confirmed = "SPLIT_CONFIRMED"
    delivered = "DELIVERED"
    refund = "REFUND"
    customer_change = "CUSTOMER_CHANGE"

# --- Agent Input Models (Pydantic) ---
# These models define the expected inputs for each agent,
# ensuring type safety and validation.
class PaymentAgentInput(BaseModel):
    payment: Dict[str, Any]
    order_total: float
    user_prefs: Dict[str, Any]

class ReputationAgentInput(BaseModel):
    courier_candidate_id: str
    historical_kpis: Dict[str, Any]

class CourierBreakdownInput(BaseModel):
    courier_id: str
    telemetry: Dict[str, Any]
    route: Dict[str, Any]

class CapacityAgentInput(BaseModel):
    order_id: str
    courier_id: str

class SplitDeliveryInput(BaseModel):
    order_id: str
    customer_response: str
    overflow_items: List[str]
    courier_pool: List[Dict[str, Any]]
    policy_split_rules: Dict[str, Any]
    user_prefs: Dict[str, Any]

class WeatherAgentInput(BaseModel):
    courier_location: str
    destination_city: str

class MerchantStatusInput(BaseModel):
    merchant_id: str
    items: List[Dict[str, Any]] = Field(..., min_items=1)

class DeliveryDispatchInput(BaseModel):
    pickup_location: Dict[str, float]
    drop_location: Dict[str, float]
    readiness_eta_min: int
    priority_flag: bool

class RerouteInput(BaseModel):
    reason: str
    current_courier: Optional[str] = None
    candidate_pool: Optional[List[Dict[str, Any]]] = None
    weather_advice: Optional[str] = None

class CustomerChangeInput(BaseModel):
    request: Dict[str, Any]
    courier_position: Dict[str, float]
    policy_change_rules: Dict[str, Any]

class PolicyGuardInput(BaseModel):
    eta_min: int
    sla_eta_min: int
    price_delta: float
    credits: float
    split_plan: Dict[str, Any]
    change_fees: float

class NotifyAgentInput(BaseModel):
    event: NotificationEvent
    payload: Dict[str, Any]
    target: List[str]

class AuditAgentInput(BaseModel):
    thoughts: List[str]
    events: List[str]
    state_diff: Dict[str, Any]

# --- Global Agent State ---
class AgentState(BaseModel):
    """The global state for the entire agentic system."""
    messages: List[BaseMessage] = Field(default_factory=list)
    order_details: Dict[str, Any] = Field(default_factory=dict)
    audit_log: List[Dict[str, Any]] = Field(default_factory=list)