"""Modelos de dados (dataclasses) usados pelo Flight Tracker."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class FlightPrice:
    id: Optional[int]
    origin: str
    destination: str
    departure_date: str
    return_date: str
    price: float
    airline: str
    departure_time: Optional[str]
    arrival_time: Optional[str]
    duration_minutes: Optional[int]
    direct: bool
    link: Optional[str]
    source: str
    timestamp: str


@dataclass
class Alert:
    id: Optional[int]
    alert_type: str
    message: str
    recipient: str
    sent_at: str
    sent: bool


@dataclass
class PriceTrend:
    id: Optional[int]
    origin: str
    destination: str
    departure_date: str
    return_date: str
    min_price: float
    max_price: float
    avg_price: float
    timestamp: str
